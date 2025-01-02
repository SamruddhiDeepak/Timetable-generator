import streamlit as st
import os
import json
import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up the Gemini API
genai.configure(api_key="AIzaSyDw00wmS7RyVjMSgkNIwK6ct6Iyx92DQq4")

# File to store tasks
TASKS_FILE = "tasks.json"

# Function to load tasks from JSON file
def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as file:
            tasks = json.load(file)
            for task in tasks:
                if 'recurrence' not in task:
                    task['recurrence'] = 'None'
            return tasks
    return []

# Function to save tasks to JSON file
def save_tasks(tasks):
    with open(TASKS_FILE, "w") as file:
        json.dump(tasks, file, indent=4)

# Function to handle recurring tasks
def handle_recurring_tasks(tasks):
    today = datetime.date.today()
    expanded_tasks = []
    for task in tasks:
        if task['recurrence'] == 'Daily':
            expanded_tasks.append(task)
        elif task['recurrence'] == 'Weekly' and today.weekday() == 0:  # Weekly tasks on Monday
            expanded_tasks.append(task)
        else:
            expanded_tasks.append(task)
    return expanded_tasks

# Function to generate the timetable
def generate_timetable(available_time, tasks, meal_times):
    prompt = f"You are a productivity coach. You have the following information:\n"
    prompt += f"Available Time: {available_time['start_time']} to {available_time['end_time']}\n"
    prompt += "Mealtimes (Do not allocate tasks during these times):\n"

    for meal in meal_times:
        prompt += f"{meal['name']}: {meal['start_time']} to {meal['end_time']}\n"

    prompt += "Tasks:\n"
    for idx, task in enumerate(tasks):
        prompt += f"{idx + 1}. {task['name']} - Priority: {task['priority']}, Duration: {task['duration']} minutes, Deadline: {task['deadline']}\n"

    prompt += "Please generate only the timetable for the day, without any additional text or explanation. Just list the tasks and the allocated times. Make sure to include enough breaks to prevent burnout. DO NOT ALLOCATE DURING MEAL TIMES"

    try:
        # Generate timetable using Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        timetable = response.text.strip().split("\n")
        return timetable
    except Exception as e:
        return [f"Error generating timetable: {e}"]

# Function to add or edit a task
def add_or_edit_task(task=None):
    task_name = st.text_input('Task Name', value=task.get('name', '') if task else '')
    task_priority = st.selectbox('Priority', ['URGENT', 'IMPORTANT', 'CAN WAIT'],
                                 index=['URGENT', 'IMPORTANT', 'CAN WAIT'].index(task['priority']) if task else 0)
    task_duration = st.number_input('Duration (in minutes)', min_value=1, max_value=480, value=task['duration'] if task else 30)
    # Handling the task deadline input, ensuring task['deadline'] is not None or invalid
    task_deadline = None
    if task and task.get('deadline') and task['deadline'] != 'None':
        try:
            task_deadline = datetime.date.fromisoformat(task['deadline'])
        except ValueError:
            task_deadline = None
    
    task_deadline = st.date_input("Deadline", value=task_deadline)
    task_recurrence = st.selectbox('Recurrence', ['None', 'Daily', 'Weekly'],
                                   index=['None', 'Daily', 'Weekly'].index(task.get('recurrence', 'None')) if task else 0)
    task_completed = st.checkbox('Mark as Completed', value=task.get('completed', False) if task else False)

    return {
        "name": task_name,
        "priority": task_priority,
        "duration": task_duration,
        "deadline": str(task_deadline) if task_deadline else None,
        "recurrence": task_recurrence,
        "completed": task_completed
    }

# Streamlit App
def app():
    st.title('Timetable Generator: Your Day, Your Way ✨📅')

    tasks = load_tasks()

    # Input section for available time
    st.write('Let\'s get this schedule rolling! Set your Start Time ⏰ to kick things off and your End Time 🛑 to wrap it up. Time to make those goals happen!💪')
    start_time = st.time_input('Start Time', value=None, step=datetime.timedelta(minutes=15))
    end_time = st.time_input('End Time', value=None, step=datetime.timedelta(minutes=15))
    if start_time is not None and end_time is not None:
        available_time = {
            "start_time": start_time.strftime('%H:%M'),
            "end_time": end_time.strftime('%H:%M')
        }
    else:
        st.write("Please select both start and end times.")

    # Input section for meal times
    st.subheader('Pick your meal times!!🍛')
    st.write('Time to set your meal times and make sure you’re fueling up at the right moments to keep your day on track! 🍽️')
    meal_times = []
    if st.checkbox('Add Mealtimes'):
        for i in range(3):  # Allow up to 3 meals
            meal_name = st.text_input(f"Meal {i + 1} Name", key=f"meal_name_{i}")
            meal_start_time = st.time_input(f"Meal {i + 1} Start Time", value=None, key=f"meal_start_{i}")
            meal_end_time = st.time_input(f"Meal {i + 1} End Time", value=None, key=f"meal_end_{i}")
            if meal_name and meal_start_time is not None and meal_end_time is not None:
                meal_times.append({
                    "name": meal_name,
                    "start_time": meal_start_time.strftime('%H:%M'),
                    "end_time": meal_end_time.strftime('%H:%M')
                })

    # Add/Edit Tasks
    st.subheader('Task time!!🗒️')
    st.write('Let’s get those tasks sorted! Add, edit, and stay on top of it all!📝⚡')
    selected_task = None
    if st.checkbox('Edit an existing task'):
        task_names = [task['name'] for task in tasks]
        selected_task_name = st.selectbox('Select a task to edit', task_names)
        selected_task = next((task for task in tasks if task['name'] == selected_task_name), None)

    task = add_or_edit_task(selected_task)
    if st.button('Save Task'):
        if selected_task:
            if task["completed"]:
                tasks.remove(selected_task)
                st.success(f"Task '{selected_task['name']}' marked as completed and removed!")
            else:
                tasks[tasks.index(selected_task)] = task
                st.success("Task updated successfully!")
        else:
            tasks.append(task)
            st.success("Task added successfully!")
        save_tasks(tasks)

    # Display task list
    if tasks:
        st.subheader('Tasks Mode: ACTIVATED⚡')
        for idx, task in enumerate(tasks, 1):
            st.write(f"{idx}. {task['name']} - {task['priority']} - {task['duration']} mins - Deadline: {task['deadline']} - Recurrence: {task['recurrence']}")

    # Generate Timetable Button
    if st.button('Generate Timetable'):
        if not tasks:
            st.warning('Please add some tasks first!')
        else:
            all_tasks = handle_recurring_tasks(tasks)
            timetable = generate_timetable(available_time, all_tasks, meal_times)
            st.subheader('Time to Own Your Day 💪')
            timetable_str = "\n".join(timetable)
            for entry in timetable:
                st.write(entry)

            st.download_button(
                label="Download Timetable",
                data=timetable_str,
                file_name="timetable.txt",
                mime="text/plain"
            )

# Run the app
if __name__ == '__main__':
    app()
