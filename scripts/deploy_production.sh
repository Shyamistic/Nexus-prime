#!/bin/bash
# Production Deployment Script for Microsoft Imagine Cup
# Deploys Nexus Prime to Azure App Service

set -e

echo "🚀 NEXUS PRIME - PRODUCTION DEPLOYMENT"
echo "======================================"

# Configuration
RESOURCE_GROUP="nexus-prime-rg"
LOCATION="eastus"
APP_NAME="nexus-prime-app"
PLAN_NAME="nexus-prime-plan"
STORAGE_ACCOUNT="nexusprimestore$(date +%s)"
COSMOS_ACCOUNT="nexus-prime-cosmos"

echo "📋 Deployment Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   App Name: $APP_NAME"
echo "   Storage: $STORAGE_ACCOUNT"

# Step 1: Create Resource Group
echo "🏗️  Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Step 2: Create App Service Plan
echo "📱 Creating App Service Plan..."
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# Step 3: Create Web App
echo "🌐 Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --name $APP_NAME \
  --runtime "PYTHON:3.11"

# Step 4: Create Storage Account
echo "💾 Creating Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Get storage connection string
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv)

# Step 5: Create Cosmos DB Account
echo "🗄️  Creating Cosmos DB..."
az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --default-consistency-level Session \
  --locations regionName=$LOCATION failoverPriority=0 isZoneRedundant=False

# Create Cosmos DB database
az cosmosdb sql database create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name nexus-db

# Create containers
containers=("incidents" "events" "actions" "users" "tenants" "invitations" "usage")
for container in "${containers[@]}"; do
  echo "📦 Creating container: $container"
  az cosmosdb sql container create \
    --account-name $COSMOS_ACCOUNT \
    --database-name nexus-db \
    --resource-group $RESOURCE_GROUP \
    --name $container \
    --partition-key-path "/id" \
    --throughput 400
done

# Get Cosmos connection details
COSMOS_ENDPOINT=$(az cosmosdb show \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query documentEndpoint \
  --output tsv)

COSMOS_KEY=$(az cosmosdb keys list \
  --name $COSMOS_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query primaryMasterKey \
  --output tsv)

# Step 6: Configure App Settings
echo "⚙️  Configuring Application Settings..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
    COSMOS_KEY="$COSMOS_KEY" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION" \
    SECRET_KEY="$(openssl rand -base64 32)" \
    JWT_SECRET_KEY="$(openssl rand -base64 32)" \
    USE_MOCK_SERVICES="false" \
    REMEDIATION_ENABLED="true" \
    REMEDIATION_DRY_RUN="false"

# Step 7: Deploy Application
echo "🚀 Deploying Application..."
cd backend
zip -r ../nexus-prime.zip . -x "*.pyc" "__pycache__/*" ".env"
cd ..

az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src nexus-prime.zip

# Step 8: Configure Custom Domain (Optional)
echo "🌐 Application deployed successfully!"
echo "📱 App URL: https://$APP_NAME.azurewebsites.net"
echo "📚 API Docs: https://$APP_NAME.azurewebsites.net/docs"

# Step 9: Health Check
echo "🏥 Performing Health Check..."
sleep 30  # Wait for app to start

HEALTH_URL="https://$APP_NAME.azurewebsites.net/health"
if curl -f -s $HEALTH_URL > /dev/null; then
  echo "✅ Health check passed!"
else
  echo "⚠️  Health check failed - app may still be starting"
fi

# Step 10: Display Connection Info
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "📱 Application URL: https://$APP_NAME.azurewebsites.net"
echo "📚 API Documentation: https://$APP_NAME.azurewebsites.net/docs"
echo "🗄️  Cosmos DB: $COSMOS_ENDPOINT"
echo "💾 Storage Account: $STORAGE_ACCOUNT"
echo ""
echo "🔑 Next Steps:"
echo "1. Configure your Azure OpenAI credentials in App Settings"
echo "2. Set up Slack/Teams webhook URLs for notifications"
echo "3. Configure custom domain if needed"
echo "4. Set up monitoring and alerts"
echo ""
echo "🏆 Ready for Microsoft Imagine Cup presentation!"

# Cleanup deployment files
rm -f nexus-prime.zip

echo "✅ Deployment script completed successfully!"