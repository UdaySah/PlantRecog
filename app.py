from __future__ import division, print_function
from __future__ import print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
import src.labels as l
from flask import jsonify
import json

# Keras
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image


# Flask utils
from flask import Flask, redirect, url_for, request, render_template, flash
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

#imprt Pyodbc for database connection to SQL Server
import pyodbc 
conn = pyodbc.connect(
	"Driver={SQL Server};"
	"Server=DESKTOP-HKQ9P0E\MSSQLSERVER01;"
	"Database=PlantRecog;"
	"Trusted_Connection=yes;"
)

# Define a flask app
app = Flask(__name__)
app.secret_key = 'Flask Error'

# Model saved with Keras model.save()
MODEL_PATH ='models/PlantRecog.h5'

# Load your trained model
model = load_model(MODEL_PATH)
# Print Now Model Ready to Serve
print('Model loaded. Start serving...')
 
# Model Predict function  
def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(50,50,1), color_mode = "grayscale")
    # Preprocessing the image
    x = image.img_to_array(img)
    x = np.true_divide(x, 255)
    x = np.expand_dims(x, axis=0)
    preds = model.predict(x)
    return preds

#Show Probability Function 
def model_predict_proba(img_path, model):
    img = image.load_img(img_path, target_size=(50,50,1), color_mode = "grayscale")
    # Preprocessing the image
    x = image.img_to_array(img)
    x = np.true_divide(x, 255)
    x = np.expand_dims(x, axis=0)
    predsproba = model.predict_proba(x)
    return predsproba

# Read Plant Species Description Function 	
def Read_Description(conn,Plant_Name):
    print("Retrieving Description");
    cursor = conn.cursor()
    cursor.execute("SELECT Description FROM Plant_Details WHERE Plant_Name = '"+Plant_Name+"'")
    for row in cursor:
	    return row

#for imageclassification
@app.route('/imageclassification', methods=['GET','POST'])
def imageclassification():
    return render_template('imageclassification.html')


# For image post and Predict Function 
@app.route('/predict', methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		# Get the file from post request
		f = request.files['file']
		# Save the file to ./uploads
		basepath = os.path.dirname(__file__)
		file_path = os.path.join(
			basepath, 'uploads', secure_filename(f.filename))
		f.save(file_path)
		# Make prediction
		predction_precent = model_predict_proba(file_path, model)
		print(predction_precent)
		preds = model_predict(file_path, model)
		pred_class = np.argmax(preds[0])
		result = str(l.labels[pred_class])
		descp = Read_Description(conn,result)
		descp = str(descp)
		return (result + "\n" + descp) 
		

# home endpoint 
@app.route('/home')
def home():
	return render_template('home.html')

# aboutus endpoint 
@app.route('/aboutus', methods=['GET','POST'])
def aboutus():
	return render_template('aboutus.html')
	
	
#remening code 
@app.route('/ViewLeafData', methods=['GET','POST'])
def ViewLeafData():
	try: 
		cursor = conn.cursor()
		cursor.execute("select * from Plant_Details")
		data = cursor.fetchall() #data from database
		cursor.close()
	except:
		print("Something Wrong in View_reports Function")
	return render_template('ViewLeafData.html',value=data)
	
	
@app.route('/UpdateLeafData', methods=['GET','POST'])
def UpdateLeafData():
	msg = ""
	cursor = conn.cursor()
	cursor.execute("select * from Plant_Details")
	data = cursor.fetchall() #data from database
	cursor.close()
	if request.method == "POST":
		SN = request.form.get('SN')
		Plant_Name = request.form.get('Plant_Name')
		Description = request.form.get('Description')
		Plant_Avaliability = request.form.get('Plant_Avaliability')
		print(SN,Plant_Name,Description,Plant_Avaliability)
		cursor = conn.cursor()
		cursor.execute("update Plant_Details set Plant_Name = '"+Plant_Name+"',  Description= '"+Description+"',Plant_Avaliability='"+Plant_Avaliability+"' where SN ='"+SN+"' ;")
		cursor.commit()
		msg = "successfully Updated SN: " + SN
		cursor.close()
		cursor = conn.cursor()
		cursor.execute("select * from Plant_Details")
		data = cursor.fetchall() #data from database
		cursor.close()
	return render_template('UpdateLeafData.html',msg=msg, value=data)

@app.route('/ViewMessages', methods=['GET','POST'])
def ViewMessages():
	try: 
		cursor = conn.cursor()
		cursor.execute("select * from Contacts")
		data = cursor.fetchall() #data from database
		cursor.close()
	except:
		print("Something Wrong in View_reports Function")
	return render_template('ViewMessages.html',value=data)
	
	

# Signlog Endpoint 	
@app.route('/signlog', methods=['GET','POST'])
def signlog():
	msg = ''
	susmsg =''
	userexists=''
	pwderror=""
	erroruser = ""
	nameunvalid = ""
	emailunvalid = ""
	if request.method == "POST":
		# Register or SignUP Form Backend 
		if request.form['action'] == 'Register':
			name = request.form.get('name')
			email = request.form.get('email')
			password = request.form.get('password')
			cpassword = request.form.get('cpassword')
			print(name,email,password,cpassword)
			if(request.form.get('name') != "" and  request.form.get('email') !="" and request.form.get('password')!="" and request.form.get('cpassword')!="" ):
				print("empty check")
				# Name Validation
				if(is_name_valid(name)):
					# Eamil Validation 
					if(is_email_address_valid(email)):
						if (password == cpassword):
							print("password checked")
							cursor = conn.cursor()
							cursor.execute("SELECT * FROM Users WHERE name = ?",(name))
							if cursor.fetchone() is not None:
								userexists = " " + name + " Already Exists"
								cursor.close()
							else:
								cursor.execute("insert into Users(name, email, password) values('"+str(name)+"','"+str(email)+"','"+str(password)+"');")
								conn.commit()
								print("Success")
								susmsg = name + " user Account has been created"
						else:
							pwderror = "Password and Confirm password Doesnot Match "
					else:
						emailunvalid = "Email is Not Valid"
				else:
					nameunvalid = "Name is not Valid"
			else:
				msg="Required Field"
		# SignIN Form Backend 
		elif request.form['action'] == 'LogIN':
			if(request.method =='POST'):
				email = request.form.get('email')
				password = request.form.get('password')
				if(email == "admin@gmail.com" and password == "admin"):
					return redirect(url_for('ViewLeafData'))
					#return render_template('ViewLeafData.html')
				else: 
					cursor = conn.cursor()
					cursor.execute("SELECT email,password from Users WHERE email = '"+email+"' AND password = '"+password+"'")
					# Fetch one record and return result
					for row in cursor: 
						if (email ==row[0] and password==row[1]): 
							flash('You were successfully logged in')
							return redirect(url_for('imageclassification'))
					else:
						# Account doesnt exist or Email/password incorrect
						erroruser = 'Email and Password Doesnot Match !!!!'
			print("for login")
	return render_template('signlog.html',msg=msg,susmsg=susmsg,userexists=userexists,pwderror=pwderror,erroruser=erroruser)


def is_email_address_valid(email):
	# Email Validation using regex 
    if not re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$", email):
        return False
    return True
def is_name_valid(name):
	# Name Validation using regex 
    if not re.match("^[a-zA-Z]*$", name):
        return False
    return True

# contact Endpoint
@app.route('/contact', methods=['GET','POST'])
def contact():
	success = ""
	error = ""
	empty = ""
	emailerror= ""
	nameerror = "" 
	if(request.method =='POST'):
		name = request.form.get('name')
		email = request.form.get('email')
		message = request.form.get('message')
		#empty Validation 
		if(request.form.get('name') != "" and  request.form.get('email') !="" and request.form.get('message')!=""):
			# Name Validation
			if(is_name_valid(name)):
				# Eamil Validation 
				if(is_email_address_valid(email)):
					if True:
						cursor = conn.cursor()
						cursor.execute("insert into Contacts(name, email, message) values('"+str(name)+"','"+str(email)+"','"+str(message)+"');")
						cursor.commit()
						success = "Message Send Successfully..."
					else:
						error = "Inserting Error in a Database"
				else:
					emailerror = "Email is Not Valid"
			else:
				nameerror= "Name is Not Valid"
		else:
			empty = "Field are Required..."
	return render_template('contact.html',success=success, error=error, empty=empty,emailerror=emailerror,nameerror=nameerror)


# Forget Password Endpoint	
@app.route('/password_forget', methods=['GET','POST'])
def password_forget():
	psw = ""
	erroruser = ""
	if(request.method =='POST'):
		email = request.form.get('email')
		cursor = conn.cursor()
		cursor.execute("SELECT email, password from Users WHERE email = '"+email+"'")
		for row in cursor:
			print(row)
			if(email == row[0]):
				psw = row[1]	
			else:
				erroruser = "Invalid Email Address"
	return render_template('password_forget.html',psw=psw,erroruser=erroruser)
if __name__=='__main__':
	http_server = WSGIServer(('', 5000), app)
	http_server.serve_forever()
	app.run(debug=True)