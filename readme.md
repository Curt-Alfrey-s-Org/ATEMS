Free open source project

in Dev mode

clone the repo and run these commands from the ATEMS directory, once python and pip are installed on Windows 10:
`pip install --upgrade -r requirements.txt`
`$env:FLASK_APP="atems:create_app"`
`flask db init`
`python atems.py`


ATEMS - Automated Tool and Equipment Management System

Overview:

ATEMS is an inventory control software for tools rooms, warehouses, supply chain operations. 

I am a US Air Force (F-16 crew chief) Vet who has worked in the tool room/supplychain supervisor postion, also in farming, trucking, retail, nuclear, cyber sec industries. This software will be advanced enough to work in any of those enviroments or for a small business too.

The approach here is to be as modularized as possible. Where the basic program stays the same and you just plug-in the modules you need for your particular industry. 


here is the home.html as a ref to the rough layout of the program 
`Win10_install/templates/home.html`

Automated - makes accountability easy with integrated email reminders sent to customers to bring back items on time. Also sends out emails to prevent jobs from being done with tools and/or equipment overdue for calibration. 

Barcode tracking - incorporates active/passive RFID barcoding with scan-gun or phone/tablet app. 


ATEMS Tracks:

where is the item stored
who checked in/out
what job it was used on
how long it has been checked out
what condition it was at check in/out
does it require calibration
does it have a shelf life




Equipment - 

records all calibrated and non-calibrated electronic test equipment, 
records historical serviceability data,
records info on calibration vendors,
ensures compliance to NIST standards and record keeping practices.



Management –

manages all types of inventory with one program.



Simple -

Reports made easy. Filter and sort the categories needed using pre-generated or custom reports to meet all business needs.

Prints or emails PDF of any report.
 


Reports:

Tool Usage History

Calibration History

User Activity History

Inventory Status Report

Generate a custom report

Issues and Feedback:



If you encounter any issues or have feedback, please create an issue on the GitHub repository.

Happy tracking with ATEMS!

I dont know it all about inventory software. and am new to github and programming so if there's any help you can give or a industry you can make a module for that would be great! 
