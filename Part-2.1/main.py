from utils import generate_email_preview, load_data, save_data, calculate_attendance, find_non_compliant_issues, change_date_format_and_save
import pandas as pd
from collections import defaultdict
import os


script_dir = os.path.dirname(os.path.abspath(__file__))

# Relative paths
sales_data_path = os.path.join(script_dir, 'SalesData.csv')
contacts_path = os.path.join(script_dir, 'Contacts.csv')
ada_cnp_fl_path = os.path.join(script_dir, 'ADA_CNP_FL.txt')
ada_cnp_la_path = os.path.join(script_dir, 'ADA_CNP_LA.txt')
ada_cnp_midland_path = os.path.join(script_dir, 'ADA_CNP_MIDLAND.txt')
ada_cnp_oh_path = os.path.join(script_dir, 'ADA_CNP_OH.txt')
ada_cnp_path = os.path.join(script_dir, 'ADA_CNP.txt')
cleaned_sales_data_path = os.path.join(script_dir, 'Cleaned_SalesData.csv')

# Loading files
sales_data = load_data(sales_data_path)
contacts = load_data(contacts_path)  
ada_cnp_fl = load_data(ada_cnp_fl_path, delimiter='\t')
ada_cnp_la = load_data(ada_cnp_la_path, delimiter='\t')
ada_cnp_midland = load_data(ada_cnp_midland_path, delimiter='\t')
ada_cnp_oh = load_data(ada_cnp_oh_path, delimiter='\t')
ada_cnp = load_data(ada_cnp_path, delimiter='\t')

# Cleaning sales data for more accurate comparison and saving it to a new file
sales_data['SCHOOLNAME'] = sales_data['Campus'] + ' ' + sales_data['Site']
sales_data = sales_data[['SCHOOLNAME','Region','SaleDate', 'MealType', 'TotalMealCount']]
save_data(sales_data, cleaned_sales_data_path, delimiter=',')
cleaned_sales_data = load_data(cleaned_sales_data_path)


# Formatting Midland data (combining Middle School and College Prep data)
def format_midland_data(df):
    if 'ABSENCES' in df.columns:
        df['ABSENCES'] = df['ABSENCES'].apply(lambda x: int(round(x)))
    return df

if not ada_cnp_midland.empty:
    midland_combined = ada_cnp_midland[ada_cnp_midland['SCHOOLNAME'].isin(['IDEA Travis Middle School', 'IDEA Travis College Prep'])].copy()
    if 'MEMBERSHIP' in midland_combined.columns and 'ABSENCES' in midland_combined.columns:
        midland_combined['SCHOOLNAME'] = 'IDEA Travis College Prep'
        midland_grouped = midland_combined.groupby(['ATTDATE', 'SCHOOLNAME']).agg({
            'MEMBERSHIP': 'sum',
            'ABSENCES': 'sum',
        }).reset_index()
    else:
        midland_grouped = pd.DataFrame()
    
    midland_academy = ada_cnp_midland[~ada_cnp_midland['SCHOOLNAME'].isin(['IDEA Travis Middle School', 'IDEA Travis College Prep'])]
    midland_final = pd.concat([midland_academy, midland_grouped], ignore_index=True)
    midland_final = format_midland_data(midland_final)

    # Calculating attendance for Midland 
    midland_final = calculate_attendance(midland_final, 'ADA_CNP_MIDLAND')
    save_data(midland_final, ada_cnp_midland_path, delimiter='\t')
    ada_cnp_midland = load_data(ada_cnp_midland_path, delimiter='\t')

# Cleaning up date format for easier search
change_date_format_and_save(ada_cnp_fl, 'ATTDATE', ada_cnp_fl_path)
change_date_format_and_save(ada_cnp_la, 'ATTDATE', ada_cnp_la_path)
change_date_format_and_save(ada_cnp_midland, 'ATTDATE', ada_cnp_midland_path)
change_date_format_and_save(ada_cnp_oh, 'ATTDATE', ada_cnp_oh_path)
change_date_format_and_save(ada_cnp, 'ATTDATE', ada_cnp_path)
change_date_format_and_save(cleaned_sales_data, 'SaleDate', cleaned_sales_data_path)

# Func. call for calculating attendance
ada_cnp_fl = calculate_attendance(ada_cnp_fl, 'ADA_CNP_FL')
ada_cnp_la = calculate_attendance(ada_cnp_la, 'ADA_CNP_LA')
ada_cnp_oh = calculate_attendance(ada_cnp_oh, 'ADA_CNP_OH')
ada_cnp = calculate_attendance(ada_cnp, 'ADA_CNP')

ada_data = pd.concat([ada_cnp_fl, ada_cnp_la, ada_cnp_midland, ada_cnp_oh, ada_cnp], ignore_index=True)

# Func. call for finding non-compliant issues
non_compliant_issues = find_non_compliant_issues(cleaned_sales_data, ada_data)

# Aggregate non-compliant issues by school
school_issues = defaultdict(list)
for issue in non_compliant_issues:
    school_issues[issue['schoolname']].append(issue)

# Generate and save email previews for non-compliant issues per school
generate_email_preview(school_issues, contacts)
