from datetime import datetime, timedelta
from atems import create_app

def choose_category(categories):
    print("Choose a category:")
    for index, category in enumerate(categories, start=1):
        print(f"{index}. {category['category']}")
    choice = int(input("Enter the number corresponding to your choice: "))
    return categories[choice - 1]


def choose_subcategory(subcategories):
    print("Choose a subcategory:")
    for index, subcategory in enumerate(subcategories, start=1):
        print(f"{index}. {subcategory}")
    choice = int(input("Enter the number corresponding to your choice: "))
    return subcategories[choice - 1]


def choose_tool(tools):
    print("Choose a tool:")
    for index, tool in enumerate(tools, start=1):
        print(f"{index}. {tool.name}")
    print(f"{len(tools) + 1}. Create a new tool")
    print(f"{len(tools) + 2}. Go back")
    choice = int(input("Enter the number corresponding to your choice: "))
    if choice == len(tools) + 1:
        return None
    elif choice == len(tools) + 2:
        return "Go back"
    else:
        return tools[choice - 1]


def add_category():
    new_category = input("Enter the name of the new category: ")
    new_subcategories = input("Enter subcategories (comma-separated): ").split(",")
    return {"category": new_category, "subcategories": new_subcategories}


def add_subcategory(existing_categories):
    category_choice = choose_category(existing_categories)
    new_subcategory = input("Enter the name of the new subcategory: ")
    category_choice['subcategories'].append(new_subcategory)
    return category_choice


def add_tool(category, subcategory):
    new_tool_name = input("Enter the name of the new tool: ")
    new_tool_size = input("Enter the size of the new tool: ")
    new_tool_location = input("Enter the location of the new tool: ")
    new_tool_status = input("Enter the status of the new tool: ")
    new_tool_calibration_date = datetime.now()
    new_tool_calibration_cycle_time = timedelta(days=30)  # Change this to appropriate cycle time
    new_tool = Tools(
        category=category,
        subcategory=subcategory,
        name=new_tool_name,
        size=new_tool_size,
        location=new_tool_location,
        status=new_tool_status,
        calibration_date=new_tool_calibration_date,
        calibration_cycle_time=new_tool_calibration_cycle_time,
        calibration_due_date=new_tool_calibration_date + new_tool_calibration_cycle_time
    )
    return new_tool


app = create_app()
with app.app_context():
    categories = [
        {"category": "Hand Tools", "subcategories": ["Hammer", "Screwdriver", "Pliers"]},
        {"category": "Power Tools", "subcategories": ["Drill", "Circular Saw", "Angle Grinder"]},
        # Add more categories here
    ]
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Add a category")
        print("2. Add a subcategory")
        print("3. Add a tool")
        print("4. Exit")
        choice = int(input("Enter your choice: "))
        
        if choice == 1:
            new_category = add_category()
            categories.append(new_category)
            print("Category added successfully.")
        elif choice == 2:
            category = add_subcategory(categories)
            print("Subcategory added successfully.")
        elif choice == 3:
            category_choice = choose_category(categories)
            subcategory_choice = choose_subcategory(category_choice['subcategories'])
            specific_tools = Tools.query.filter_by(category=category_choice['category'], subcategory=subcategory_choice).all()
            tool_choice = choose_tool(specific_tools)
            if tool_choice == "Go back":
                continue
            elif tool_choice is None:
                new_tool = add_tool(category_choice['category'], subcategory_choice)
                db.session.add(new_tool)
                db.session.commit()
                print("Tool added successfully.")
            else:
                # Do something with the chosen tool
                pass
        elif choice == 4:
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
