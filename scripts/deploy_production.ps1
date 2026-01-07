# PowerShell Deployment Script for Microsoft Imagine Cup
# Deploys Nexus Prime to Azure App Service

Write-Host "🚀 NEXUS PRIME - PRODUCTION DEPLOYMENT" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Configuration
$RESOURCE_GROUP = "nexus-prime-rg"
$LOCATION = "eastus"
$APP_NAME = "nexus-prime-$(Get-Random -Minimum 1000 -Maximum 9999)"
$PLAN_NAME = "nexus-prime-plan"
$STORAGE_ACCOUNT = "nexusstore$(Get-Random -Minimum 100000 -Maximum 999999)"
$COSMOS_ACCOUNT = "nexus-cosmos-$(Get-Random -Minimum 1000 -Maximum 9999)"

Write-Host "📋 Deployment Configuration:" -ForegroundColor Yellow
Write-Host "   Resource Group: $RESOURCE_GROUP" -ForegroundColor White
Write-Host "   Location: $LOCATION" -ForegroundColor White
Write-Host "   App Name: $APP_NAME" -ForegroundColor White
Write-Host "   Storage: $STORAGE_ACCOUNT" -ForegroundColor White

# Check if Azure CLI is installed
try {
    $null = az --version
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install: https://aka.ms/installazurecliwindows" -ForegroundColor Red
    exit 1
}

# Check if logged in
$account = az account show 2>$null
if (-not $account) {
    Write-Host "🔐 Please login to Azure..." -ForegroundColor Yellow
    az login
}

# Step 1: Create Resource Group
Write-Host "🏗️  Creating Resource Group..." -ForegroundColor Cyan
az group create --name $RESOURCE_GROUP --location $LOCATION

# Step 2: Create App Service Plan
Write-Host "📱 Creating App Service Plan..." -ForegroundColor Cyan
az appservice plan create --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku B1 --is-linux

# Step 3: Create Web App
Write-Host "🌐 Creating Web App..." -ForegroundColor Cyan
az webapp create --resource-group $RESOURCE_GROUP --plan $PLAN_NAME --name $APP_NAME --runtime "PYTHON:3.11"

# Step 4: Create Storage Account
Write-Host "💾 Creating Storage Account..." -ForegroundColor Cyan
az storage account create --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard_LRS

# Get storage connection string
$STORAGE_CONNECTION = az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --query connectionString --output tsv

# Step 5: Create Cosmos DB Account
Write-Host "🗄️  Creating Cosmos DB..." -ForegroundColor Cyan
az cosmosdb create --name $COSMOS_ACCOUNT --resource-group $RESOURCE_GROUP --default-consistency-level Session --locations regionName=$LOCATION failoverPriority=0 isZoneRedundant=False

# Create Cosmos DB database
az cosmosdb sql database create --account-name $COSMOS_ACCOUNT --resource-group $RESOURCE_GROUP --name nexus-db

# Create containers
$containers = @("incidents", "events", "actions", "users", "tenants", "invitations", "usage")
foreach ($container in $containers) {
    Write-Host "📦 Creating container: $container" -ForegroundColor Yellow
    az cosmosdb sql container create --account-name $COSMOS_ACCOUNT --database-name nexus-db --resource-group $RESOURCE_GROUP --name $container --partition-key-path "/id" --throughput 400
}

# Get Cosmos connection details
$COSMOS_ENDPOINT = az cosmosdb show --name $COSMOS_ACCOUNT --resource-group $RESOURCE_GROUP --query documentEndpoint --output tsv
$COSMOS_KEY = az cosmosdb keys list --name $COSMOS_ACCOUNT --resource-group $RESOURCE_GROUP --query primaryMasterKey --output tsv

# Generate secure keys
$SECRET_KEY = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString()))
$JWT_SECRET_KEY = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString()))

# Step 6: Configure App Settings
Write-Host "⚙️  Configuring Application Settings..." -ForegroundColor Cyan
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings `
    COSMOS_ENDPOINT="$COSMOS_ENDPOINT" `
    COSMOS_KEY="$COSMOS_KEY" `
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" `
    SECRET_KEY="$SECRET_KEY" `
    JWT_SECRET_KEY="$JWT_SECRET_KEY" `
    USE_MOCK_SERVICES="false" `
    REMEDIATION_ENABLED="true" `
    REMEDIATION_DRY_RUN="false"

# Step 7: Deploy Application
Write-Host "🚀 Deploying Application..." -ForegroundColor Cyan
Set-Location ..
Compress-Archive -Path "backend\*" -DestinationPath "nexus-prime.zip" -Force
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src "nexus-prime.zip"

# Step 8: Display Results
Write-Host ""
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host "📱 App URL: https://$APP_NAME.azurewebsites.net" -ForegroundColor Yellow
Write-Host "📚 API Docs: https://$APP_NAME.azurewebsites.net/docs" -ForegroundColor Yellow
Write-Host "🗄️  Cosmos DB: $COSMOS_ENDPOINT" -ForegroundColor White
Write-Host "💾 Storage Account: $STORAGE_ACCOUNT" -ForegroundColor White

# Step 9: Health Check
Write-Host "🏥 Performing Health Check..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

try {
    $healthResponse = Invoke-WebRequest -Uri "https://$APP_NAME.azurewebsites.net/health" -TimeoutSec 10
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Health check failed - app may still be starting" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔑 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Add your Azure OpenAI credentials to App Settings" -ForegroundColor White
Write-Host "2. Configure Slack/Teams webhook URLs" -ForegroundColor White
Write-Host "3. Test the deployment with the demo script" -ForegroundColor White
Write-Host ""
Write-Host "🏆 Ready for Microsoft Imagine Cup presentation!" -ForegroundColor Green

# Save deployment info
$deploymentInfo = @"
NEXUS PRIME DEPLOYMENT INFO
===========================
App URL: https://$APP_NAME.azurewebsites.net
API Docs: https://$APP_NAME.azurewebsites.net/docs
Resource Group: $RESOURCE_GROUP
Cosmos DB: $COSMOS_ENDPOINT
Storage: $STORAGE_ACCOUNT

Deployed: $(Get-Date)
"@

$deploymentInfo | Out-File -FilePath "deployment-info.txt" -Encoding UTF8
Write-Host "📄 Deployment info saved to deployment-info.txt" -ForegroundColor Cyan

# Cleanup
Remove-Item "nexus-prime.zip" -ErrorAction SilentlyContinue

Write-Host "✅ Deployment script completed successfully!" -ForegroundColor Green