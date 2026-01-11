Right after “Multi-Tenant Authentication”, add:

text
### Judge Demo Login (Hosted MVP)

For the live Imagine Cup demo environment, use this pre-created tenant:

- **Swagger API**: https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io/docs#/
- **Dashboard**: https://white-river-06eae7700.2.azurestaticapps.net/

#### 1) Get a fresh access token (tokens expire after 30 minutes)

**Windows PowerShell:**

```powershell
# Register demo tenant (idempotent / safe to re-run)
$body = @{
  name           = "Judge Demo Tenant"
  admin_name     = "Judge Admin"
  admin_email    = "judge@local.nexus"
  admin_password = "Nexus!123"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io/api/v1/auth/register-tenant" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

# Login and capture JWT
$loginBody = @{
  email    = "judge@local.nexus"
  password = "Nexus!123"
} | ConvertTo-Json

$response = Invoke-WebRequest `
  -Uri "https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io/api/v1/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body $loginBody

$token = ($response.Content | ConvertFrom-Json).access_token
$token
Use the printed token as:

text
Authorization: Bearer <token>
If you get 401 at any point, simply re-run the login block above to obtain a new token.

text

This exactly matches what you just tested successfully in PowerShell.[1][2]

## 2. Fix support links quickly

Change the fake GitHub links under **Support** to your real repo:

```md
GitHub Issues: https://github.com/Shyamistic/Nexus-prime/issues
Discussions:   https://github.com/Shyamistic/Nexus-prime/discussions
