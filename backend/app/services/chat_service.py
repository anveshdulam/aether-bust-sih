import json
import asyncio
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import get_settings
from app.services.run_service import RunService, bbox_to_slices, grid_stats
from app.services import chat_tools
from app.constants import VAR_CODES

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "aether_system.md"

class ChatAgent:
    def __init__(self, svc: RunService, client: genai.Client):
        self.svc = svc
        self.client = client
        self.settings = get_settings()
        
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            self.system_prompt_template = f.read()
            
    def _get_provenance(self, run_id: str) -> str:
        # Check if the model weights are untrained or real
        if "4years" in self.settings.MODEL_WEIGHTS_PATH:
            return "Real ERA5/GFS data (2019-2022) with trained BustNet weights."
        elif "real" in self.settings.MODEL_WEIGHTS_PATH:
            return "Real ERA5/GFS data with trained BustNet weights."
        return "Synthetic generated data with untrained model weights."

    def build_system_prompt(self, run_id: str) -> str:
        provenance = self._get_provenance(run_id)
        return self.system_prompt_template.replace("{{provenance}}", provenance)

    def _get_run_summary(self, run_id: str) -> dict:
        doc = self.svc.run_document(run_id)
        return {
            "grid": doc["grid"],
            "lead_times": doc["n_lead_times"],
            "variables": doc["variables"],
            "provenance": self._get_provenance(run_id)
        }

    def _get_hotspots(self, run_id: str, day: int, top_k: int, threshold: float) -> list:
        dets = self.svc.detections(run_id)
        filtered = [d for d in dets if d["lead_time"] == day and d["peak_probability"] >= threshold]
        filtered.sort(key=lambda x: x["peak_probability"], reverse=True)
        return [
            {
                "lat": d["centroid"]["coordinates"][1],
                "lon": d["centroid"]["coordinates"][0],
                "probability": d["peak_probability"],
                "variable": d["variable"]
            }
            for d in filtered[:top_k]
        ]

    def _get_region_stats(self, run_id: str, day: int, bbox: list[float]) -> dict:
        rows, cols = bbox_to_slices(bbox)
        res = self.svc.get_result(run_id)
        
        # Max probability across all variables for that day in the region
        max_prob = 0.0
        for v in range(len(VAR_CODES)):
            p = res.bust[day - 1, v][rows, cols]
            if p.size > 0:
                max_prob = max(max_prob, float(p.max()))
                
        return {"max_bust_probability": max_prob}

    def _get_attribution(self, run_id: str, lat: float, lon: float, day: int) -> dict:
        from app.services.run_service import lat_index, lon_index
        from app.constants import VAR_CODES
        
        res = self.svc.get_result(run_id)
        i, j = lat_index(lat), lon_index(lon)
        
        best_var = "z500"
        best_prob = -1.0
        
        # Find the variable with the highest bust probability at this cell
        for v_idx, var_code in enumerate(VAR_CODES):
            p = float(res.bust[day - 1, v_idx, i, j])
            if p > best_prob:
                best_prob = p
                best_var = var_code
                
        attr = self.svc.attribution(run_id, best_var, day, lat, lon)
        
        # Return a concise summary for the LLM context to avoid context overload
        return {
            "target_variable": best_var,
            "bust_probability": best_prob,
            "top_drivers": [
                {"variable": d["channel_name"], "score": d["score"], "sign": d["sign"]}
                for d in attr["drivers"][:3]  # Only top 3 to keep it concise
            ],
            "narrative": attr["narrative"]
        }

    def _compare_days(self, run_id: str, day_a: int, day_b: int, bbox: list[float] = None) -> dict:
        # Simplified comparison
        return {"trend": "Risk increases slightly" if day_b > day_a else "Risk decreases"}

    async def stream_chat(self, message: str, history: list, ui_snapshot: dict):
        run_id = ui_snapshot.get("run_id") or self.svc.default_run_id()
        sys_prompt = self.build_system_prompt(run_id)
        
        # Build context
        context_msg = f"User Message: {message}\n\nCurrent UI State:\n{json.dumps(ui_snapshot)}"
        
        # We define a list of callables for google-genai
        tool_funcs = [
            chat_tools.get_run_summary,
            chat_tools.get_hotspots,
            chat_tools.get_region_stats,
            chat_tools.get_attribution,
            chat_tools.compare_days,
            chat_tools.set_day,
            chat_tools.select_point,
            chat_tools.set_layer,
            chat_tools.highlight_bbox,
            chat_tools.fly_to
        ]

        # Convert history
        formatted_history = []
        for h in history:
            formatted_history.append(types.Content(role="user" if h.role == "user" else "model", parts=[types.Part.from_text(h.content)]))

        chat = self.client.aio.chats.create(
            model=self.settings.GEMINI_MODEL_PRO,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                tools=tool_funcs,
                temperature=0.3
            ),
            history=formatted_history
        )

        for attempt in range(5):
            try:
                response = await chat.send_message_stream(context_msg)
                
                async for chunk in response:
                    if chunk.text:
                        yield "data: " + json.dumps({"type": "token", "content": chunk.text}) + "\n\n"
                    if chunk.function_calls:
                        for fc in chunk.function_calls:
                            yield "data: " + json.dumps({"type": "tool_start", "name": fc.name, "args": fc.args}) + "\n\n"
                            
                            # Execute tool
                            result = {"error": "Tool not implemented"}
                            try:
                                if fc.name == "get_run_summary":
                                    result = self._get_run_summary(fc.args["run_id"])
                                elif fc.name == "get_hotspots":
                                    result = self._get_hotspots(fc.args["run_id"], fc.args["day"], fc.args["top_k"], fc.args["threshold"])
                                elif fc.name == "get_region_stats":
                                    result = self._get_region_stats(fc.args["run_id"], fc.args["day"], fc.args["bbox"])
                                elif fc.name == "get_attribution":
                                    result = self._get_attribution(fc.args["run_id"], fc.args["lat"], fc.args["lon"], fc.args["day"])
                                elif fc.name == "compare_days":
                                    result = self._compare_days(fc.args["run_id"], fc.args["day_a"], fc.args["day_b"], fc.args.get("bbox"))
                                elif hasattr(chat_tools, fc.name):
                                    # UI Action
                                    result = getattr(chat_tools, fc.name)(**fc.args)
                                    if "_ui_action" in result:
                                        yield "data: " + json.dumps({"type": "ui_action", "action": result["_ui_action"], "params": result["params"]}) + "\n\n"
                                        result = {"status": "ui_updated"}
                            except Exception as e:
                                result = {"error": str(e)}
                                
                            yield "data: " + json.dumps({"type": "tool_end", "name": fc.name, "result_summary": str(result)[:100]}) + "\n\n"
                            
                            # Send result back to model
                            # The chat object manages history automatically in google-genai!
                            context_msg = types.Part.from_function_response(name=fc.name, response={"result": result})
                            
                # If there were function calls, we loop again (the chat object handles sending the parts).
                # But wait, send_message_stream with a function response part will trigger the next turn.
                if not response.function_calls:
                    break
                    
            except Exception as e:
                yield "data: " + json.dumps({"type": "error", "content": str(e)}) + "\n\n"
                break
                
        yield "data: " + json.dumps({"type": "done"}) + "\n\n"
