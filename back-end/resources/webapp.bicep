param location string = resourceGroup().location
param appServicePlanName string
param webAppName string
param sku string
param linuxFxVersion string = ''
param tags object = {}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: linuxFxVersion != '' ? 'linux' : 'app'
  properties: {
    reserved: linuxFxVersion != '' ? true : false
  }
}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  tags: tags
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: linuxFxVersion
    }
  }
}

output webAppHostName string = webApp.properties.defaultHostName
output webAppId string = webApp.id
