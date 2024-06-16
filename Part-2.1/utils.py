import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Function to load data files
def load_data(file_path, delimiter=','):
    try:
        print(f"Loading {file_path}...")
        df = pd.read_csv(file_path, delimiter=delimiter)
        print(f"Loaded {file_path} with {len(df)} records.")
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

# Function to save data files
def save_data(df, file_path, delimiter=','):
    try:
        print(f"Saving {file_path}...")
        df.to_csv(file_path, index=False, sep=delimiter)
        print(f"Saved {file_path}.")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

# Function to calculate attendance (Membership-Absences)
def calculate_attendance(df, name):
    if not df.empty and 'MEMBERSHIP' in df.columns and 'ABSENCES' in df.columns:
        df['ATTENDANCE'] = df['MEMBERSHIP'] - df['ABSENCES']
        print(f"Calculated attendance for {name}.")
    else:
        print(f"Missing data or columns in {name}.")
    return df

# Function to change date format and save the file
def change_date_format_and_save(df, date_column, file_path):
    try:
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce').dt.strftime('%Y-%m-%d')
        save_data(df, file_path, delimiter='\t')
    except Exception as e:
        print(f"Error changing date format for {file_path}: {e}")

# Function to find non-compliant issues
def find_non_compliant_issues(cleaned_salesdata, ada_data):
    non_compliant_issues = []

    cleaned_salesdata['SaleDate'] = pd.to_datetime(cleaned_salesdata['SaleDate'], errors='coerce').dt.strftime('%Y-%m-%d')
    ada_data['ATTDATE'] = pd.to_datetime(ada_data['ATTDATE'], errors='coerce').dt.strftime('%Y-%m-%d')

    for _, row in cleaned_salesdata.iterrows():
        schoolname = row['SCHOOLNAME']
        region = row['Region']
        saledate = row['SaleDate']
        meal_type = row['MealType']
        totalmealcount = row['TotalMealCount']

        ada_row = ada_data[(ada_data['SCHOOLNAME'] == schoolname) & (ada_data['ATTDATE'] == saledate)]

        if not ada_row.empty:
            attendance = ada_row.iloc[0]['ATTENDANCE']
            if totalmealcount > attendance:
                issue = {
                    'schoolname': schoolname,
                    'region': region,
                    'attdate': saledate,
                    'meal_type': meal_type,
                    'totalmealcount': totalmealcount,
                    'attendance': attendance
                }
                non_compliant_issues.append(issue)
                print(f"Non-compliant issue found: {issue}")
    return non_compliant_issues

# Function to generate and save email previews for non-compliant issues per school
def generate_email_preview(school_issues, contacts):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for schoolname, issues in school_issues.items():
        first_issue = issues[0]
        region = first_issue['region']
        start_date = first_issue['attdate']  
        start_date = pd.to_datetime(start_date)
        end_date = start_date + timedelta(days=6)   
            
        contact_campus = contacts[contacts['Campus'].apply(lambda x: x.lower() in schoolname.lower()) & (contacts['JobTitle'].str.contains('Cafeteria Manager'))]
        contact_region = contacts[(contacts['Region'] == region) & (contacts['JobTitle'].str.contains('Regional Manager'))]
        
        if not contact_campus.empty:
            cafeteria_manager_row = contact_campus.iloc[0]
            cafeteria_manager = cafeteria_manager_row['Name']
            manager_email = cafeteria_manager_row['Email']
        else:
            cafeteria_manager = None
            manager_email = None

        if not contact_region.empty:
            regional_manager_row = contact_region.iloc[0]
            regional_manager = regional_manager_row['Name']
            regional_manager_email = regional_manager_row['Email']
            if not manager_email:
                manager_email = regional_manager_email
        else:
            regional_manager = None
            regional_manager_email = None

        if not cafeteria_manager and not regional_manager:
            print(f"No contacts found for school: {schoolname} in region: {region}")
            continue

        issue_rows = ""
        for issue in issues:
            issue_rows += f"""
            <tr>
                <td>{issue['schoolname']}</td>
                <td>{issue['meal_type']}</td>
                <td>{issue['attdate']}</td>
                <td>{issue['totalmealcount']}</td>
                <td>{issue['attendance']}</td>
                <td>{issue['totalmealcount'] - issue['attendance']}</td>
            </tr>
            """
        
        # Email template similar to the assessment pdf...if a campus does not have a cafeteria manager, the regional manager will receive the email
       
        subject = f"Weekly Claim Review {schoolname} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"

        body = f"""
        <html>
        <body>
        <p>Good Morning {cafeteria_manager if cafeteria_manager else regional_manager},</p>
        <p>You are receiving this email because your campus had <span style="color:red; font-weight: bold;">non-compliant</span> serving days this week. Please see the serving days and meal counts below:</p>
        <p style="color: orange; font-size: larger;"><b>You will need to resolve the edit check fails by <b>{(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}</b> at <b>8:00 A.M</b></p>
        <table border="1" style="border-collapse:collapse;">
            <tr>
                <th>School</th>
                <th>MealType</th>
                <th>Claim Date</th>
                <th>Meals Claimed</th>
                <th>Attendance</th>
                <th>Meals Over</th>
            </tr>
            {issue_rows}
        </table>
        <p><b><u>NEXT STEPS:</u></b></p>
        <ol>
            <li>Generate a Menu Item Sales report for these dates and compare to your Counting and Claiming Excel to ensure your Academy and College Prep meal counts are accurate.</li>
            <li>Verify ADA for these dates with your SIS. If your SIS has a larger number for attendance, please provide us with that documentation by replying to this email.</li>
            <li>If you must edit meals, please do so before <b>{(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}</b>.</li>
            <li>If edits are made to meal counts, be sure to update your FPRs to reflect the updated meal counts.</li>
        </ol>
        <p><b>{regional_manager}</b> cc'd</p>
        </body>
        </html>
        """

        # Save the email preview to a file for testing/verification
        preview_path = os.path.join(script_dir, f"email_preview_{schoolname}_{issues[0]['attdate']}.html")
        with open(preview_path, 'w') as file:
            file.write(body)

        print(f"Email preview saved to {preview_path}")
        # If I was going to send an email, this is how I would do it. In this case, I'm using smtplib because I'm using a gmail account, if I were to use outlook, I would use win32com.client
        # sender_email = "daniella.d.thompson.com"
        # sender_password = "xxxxxxx"
        # smtp_server = "smtp.gmail.com"
        # smtp_port = 587

        # message = MIMEMultipart()
        # message['From'] = sender_email
        # message['To'] = manager_email
        # message['Cc'] = regional_manager_email
        # message['Subject'] = subject
        # message.attach(MIMEText(body, 'html'))

        # try:
        #     server = smtplib.SMTP(smtp_server, smtp_port)
        #     server.starttls()
        #     server.login(sender_email, sender_password)
        #     server.sendmail(sender_email, [manager_email, regional_manager_email], message.as_string())
        #     print(f"Email sent to {manager_email} and cc'd to {regional_manager_email}")
        # except Exception as e:
        #     print(f"Error sending email: {e}")
        # finally:
        #     server.quit()