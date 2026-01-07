$body = @{
    title = "Payment Gateway Critical Failure"
    message = "Payment processing down, 100% error rate"
    severity = "critical"
    source = "monitoring"
    tags = @("payment", "critical", "revenue-impact")
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ingest/webhook/generic" -Method Post -Body $body -ContentType "application/json"
    Write-Host "SUCCESS: Incident created"
    Write-Host "Response: $($response | ConvertTo-Json)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
}