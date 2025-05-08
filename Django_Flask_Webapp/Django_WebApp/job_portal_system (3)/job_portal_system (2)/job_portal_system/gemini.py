from google import genai

client = genai.Client(api_key="AIzaSyAcLC2IAPKFCLhQFVTblHK84oMOCs6yBhc")
company_name = "Tech Innovations Inc."
job_title = "Software Engineer"
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"Generate a job description for a {job_title} position at a Company named {company_name}.(word limit: 200)",
)

print(response.text)