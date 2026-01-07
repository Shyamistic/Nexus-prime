# Simple Azure Deployment for Nexus Prime
Write-Host "🚀 NEXUS PRIME - AZURE DEPLOYMENT" -ForegroundColor Green

# Configuration
$APP_NAME = "nexus-prime-$(Get-Random -Minimum 1000 -Maximum 9999)"
$RESOURCE_GROUP = "nexus-prime-rg"

Write-Host "📋 App Name: $APP_NAME" -ForegroundColor Yellow

# Check Azure CLI
if (!(Get-Command "az" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI not found. Install from: https://aka.ms/installazurecliwindows" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Azure CLI found" -ForegroundColor Green

# Login check
$account = az account show 2>$null
if (!$account) {
    Write-Host "🔐 Logging into Azure..." -ForegroundColor Yellow
    az login
}

# Create resource group
Write-Host "🏗️ Creating resource group..." -ForegroundColor Cyan
az group create --name $RESOURCE_GROUP --location eastus

# Create app service plan
Write-Host "📱 Creating app service plan..." -ForegroundColor Cyan
az appservice plan create --name "nexus-plan" --resource-group $RESOURCE_GROUP --sku B1 --is-linux

# Create web app
Write-Host "🌐 Creating web app..." -ForegroundColor Cyan
az webapp create --resource-group $RESOURCE_GROUP --plan "nexus-plan" --name $APP_NAME --runtime "PYTHON:3.11"

# Configure app settings
Write-Host "⚙️ Configuring app settings..." -ForegroundColor Cyan
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings USE_MOCK_SERVICES="true" SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Cyan
if (Test-Path "nexus-deploy.zip") { Remove-Item "nexus-deploy.zip" }
Compress-Archive -Path "backend\*" -DestinationPath "nexus-deploy.zip"

# Deploy
Write-Host "🚀 Deploying application..." -ForegroundColor Cyan
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src "nexus-deploy.zip"

# Results
Write-Host ""
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "📱 App URL: https://$APP_NAME.azurewebsites.net" -ForegroundColor Yellow
Write-Host "📚 API Docs: https://$APP_NAME.azurewebsites.net/docs" -ForegroundColor Yellow

# Save info
"App URL: https://$APP_NAME.azurewebsites.net" | Out-File "deployment-url.txt"
Write-Host "📄 URL saved to deployment-url.txt" -ForegroundColor Cyan

# Cleanup
Remove-Item "nexus-deploy.zip" -ErrorAction SilentlyContinue

Write-Host "✅ Done! Share the URL with judges." -ForegroundColor Green