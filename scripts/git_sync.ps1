param (
    [string]$CommitMessage = "Update real data scripts and final integration"
)

Write-Host "Syncing with Git..."
git pull origin main
git add .
git commit -m "$CommitMessage"
git push origin main
Write-Host "Git sync complete!"
