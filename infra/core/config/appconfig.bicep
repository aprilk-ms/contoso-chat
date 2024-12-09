metadata description = 'Creates an Azure App Configuration store.'
param name string
param location string = resourceGroup().location
param tags object = {}
param appInsightsId string

@description('Specifies the names of the key-value resources. The name is a combination of key and label with $ as delimiter. The label is optional.')
param keyValueNames array = []

@description('Specifies the values of the key-value resources.')
param keyValueValues array = []

resource configStore 'Microsoft.AppConfiguration/configurationStores@2023-09-01-preview' = {
  name: name
  location: location
  sku: {
    name: 'standard'
  }
  tags: tags
  properties: {
    encryption: {}
    disableLocalAuth: true
    enablePurgeProtection: false
    experimentation:{}
    dataPlaneProxy:{
      authenticationMode: 'Pass-through'
      privateLinkDelegation: 'Disabled'
    }
    telemetry: {
      resourceId: appInsightsId
    }
  }
}

resource configStoreKeyValue 'Microsoft.AppConfiguration/configurationStores/keyValues@2023-03-01' = [
  for (item, i) in keyValueNames: {
    parent: configStore
    name: item
    properties: {
      value: keyValueValues[i]
      tags: tags
    }
  }
]

output endpoint string = configStore.properties.endpoint
output name string = configStore.name
