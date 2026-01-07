# NEXUS Deployment Script
# Usage: ./scripts/deploy.ps1

$ResourceGroup = "nexus-rg"
$Location = "eastus"
$AcrName = "nexusregistry" + (Get-Random -Minimum 1000 -Maximum 9999)
$EnvName = "nexus-env"

Write-Host "🚀 Starting NEXUS Deployment..." -ForegroundColor Cyan

# 1. Login check
az account show | Out-Null
if ($?) { Write-Host "✅ Authenticated with Azure" -ForegroundColor Green }
else { Write-Host "❌ Not logged in. Run 'az login' first."; exit }

# 2. Ensure Resource Group Exists
az group create --name $ResourceGroup --location $Location | Out-Null
Write-Host "✅ Resource Group Ready" -ForegroundColor Green

# 3. Create Container Registry (ACR)
Write-Host "📦 Creating Container Registry (This may take a minute)..."
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true | Out-Null
$AcrServer = az acr show --name $AcrName --query loginServer --output tsv
$AcrUser = az acr credential show --name $AcrName --query username --output tsv
$AcrPass = az acr credential show --name $AcrName --query passwords[0].value --output tsv
Write-Host "✅ Registry Ready: $AcrServer" -ForegroundColor Green

# 4. Build & Push Backend
Write-Host "🔨 Building Backend Image..."
az acr build --registry $AcrName --image nexus-backend:latest ./backend | Out-Null
Write-Host "✅ Backend Pushed" -ForegroundColor Green

# 5. Build & Push Frontend
Write-Host "🔨 Building Frontend Image..."
az acr build --registry $AcrName --image nexus-frontend:latest ./frontend | Out-Null
Write-Host "✅ Frontend Pushed" -ForegroundColor Green

# 6. Create Container Environment
Write-Host "☁️ Creating Serverless Environment..."
az containerapp env create --name $EnvName --resource-group $ResourceGroup --location $Location | Out-Null

# 7. Deploy Backend Service
Write-Host "🚀 Deploying Backend Microservice..."
az containerapp create `
  --name nexus-backend `
  --resource-group $ResourceGroup `
  --environment $EnvName `
  --image "$AcrServer/nexus-backend:latest" `
  --target-port 8000 `
  --ingress external `
  --registry-server $AcrServer `
  --registry-username $AcrUser `
  --registry-password $AcrPass `
  --min-replicas 1 --max-replicas 10 `
  --env-vars "COSMOS_ENDPOINT=..." "COSMOS_KEY=..." "AZURE_OPENAI_API_KEY=..." | Out-Null

# 8. Deploy Frontend Service
Write-Host "🚀 Deploying Frontend Dashboard..."
az containerapp create `
  --name nexus-frontend `
  --resource-group $ResourceGroup `
  --environment $EnvName `
  --image "$AcrServer/nexus-frontend:latest" `
  --target-port 80 `
  --ingress external `
  --registry-server $AcrServer `
  --registry-username $AcrUser `
  --registry-password $AcrPass | Out-Null

Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "Your startup is live in the cloud."