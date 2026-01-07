param location string = resourceGroup().location
param appName string = 'nexus-${uniqueString(resourceGroup().id)}'

// 1. Cosmos DB Account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: '${appName}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location }]
  }
}

// 2. Database & Containers
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'nexus-db'
  properties: {
    resource: { id: 'nexus-db' }
  }
}

resource incidentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'incidents'
  properties: {
    resource: {
      id: 'incidents'
      partitionKey: { paths: ['/id'], kind: 'Hash' }
    }
  }
}

resource eventsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'events'
  properties: {
    resource: {
      id: 'events'
      partitionKey: { paths: ['/incident_id'], kind: 'Hash' }
    }
  }
}

// 3. Azure OpenAI (Cognitive Services)
resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${appName}-openai'
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: '${appName}-openai'
  }
}

// Output critical values for .env
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output openaiEndpoint string = openai.properties.endpoint