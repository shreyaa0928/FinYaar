import requests
# register a user
res = requests.post('http://127.0.0.1:5000/api/auth/register', json={
    'name':'test2', 'email':'test2@banasthali.in', 'student_id':'222', 'password':'test'
})
# mock user in backend, we need the token, but we need OTP
# Instead I will directly login via the local python interpreter hitting the database!
