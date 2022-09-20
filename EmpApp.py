from crypt import methods
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
employee_table = 'employee'
payroll_table = 'payroll'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('PayrollPage.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/changePage", methods=['GET'])
def EditPayrollPage():
    return render_template('EditPayroll.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_employee_sql = "INSERT INTO " + employee_table + " VALUES (%s, %s, %s, %s, %s)"
    insert_payroll_sql = "INSERT INTO " + payroll_table + " VALUES (%s, %s, %s, %s, %s)"

    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_employee_sql, (emp_id, first_name, last_name, pri_skill, location))
        cursor.execute(insert_payroll_sql, (emp_id, 0, 0, 0, 0))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


@app.route("/getEmpName", methods=['GET'])
def GetEmpName():
    emp_id = request.form['emp_id']

    get_fn_sql = "SELECT first_name FROM " + employee_table + " WHERE emp_id" + " = " + emp_id
    get_ln_sql = "SELECT last_name FROM " + employee_table + " WHERE emp_id" + " = " + emp_id

    cursor1 = db_conn.cursor()
    cursor2 = db_conn.cursor()

    if emp_id != "":
        cursor1.execute(get_fn_sql)
        cursor2.execute(get_ln_sql)

        first_name = cursor1.fetchone()
        last_name = cursor2.fetchone()    

    open("EditPayroll.html").read().format(name=first_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
