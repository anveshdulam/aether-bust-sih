param (
    [string]$CommitMessage = "Update real data scripts and final integration"
)

Write-Host "Syncing with Git..."
git pull origin master
git add .
git commit -m "$CommitMessage"
git push origin master
Write-Host "Git sync complete!"
