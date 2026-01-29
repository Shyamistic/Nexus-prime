How to Log In (Demo Access)

This project uses manual tenant registration via Swagger for demo and evaluation purposes.
There is no public signup UI enabled. This is intentional due to security and isolation requirements.

To access the product, you must first register a tenant using the backend Swagger API, then use the same credentials to log in to the product UI.

Step 1: Open the Swagger API Docs

Go to the backend Swagger documentation:

https://nexus-backend.nicesea-d905a880.centralindia.azurecontainerapps.io/docs#/

Step 2: Navigate to Tenant Registration

In the Swagger UI:

Scroll to the Authentication section

Locate the endpoint:

POST /api/v1/auth/register-tenant


Click “Try it out”

Step 3: Register a Demo Tenant

Use the following JSON body exactly as shown (this is for demo access only):

{
  "name": "Demo Tenant",
  "admin_email": "judge@local.nexus",
  "admin_name": "Judge",
  "admin_password": "Nexus!123"
}


Then click Execute.

Expected Result

You should receive a 200 Successful Response

This confirms the tenant and admin user have been created

If you receive a 422 Validation Error, the tenant may already exist—proceed to login.

Step 4: Open the Product Login Page

Go to the product UI:

[https://white-river-06eae7700.2.azurestaticapps.net/]

Step 5: Log In Using the Same Credentials

Use the credentials you registered in Swagger:

Email: judge@local.nexus

Password: Nexus!123

Submit the login form.

Why This Flow Exists

This manual process exists for the following reasons:

Prevents unauthorized public access

Ensures tenant isolation for demos

Keeps the system aligned with production-grade security constraints

Avoids exposing signup flows during competitions

This approach is intentional and not a limitation of the system.

Notes for Evaluators

This project was submitted to the Microsoft Imagine Cup

The Swagger-based registration is demo-only

In production, this flow would be replaced with:

Secure onboarding

Role-based access control

Email verification
