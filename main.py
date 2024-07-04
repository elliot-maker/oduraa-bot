import json
import threading
import time
import schedule
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import telebot
from telebot import types
import os
import urllib3.exceptions
from flask import Flask, request
import random
import openai
import speech_recognition as sr
from pydub import AudioSegment
import io
from gtts import gTTS
import re
import requests
from PIL import Image
from io import BytesIO
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

app = Flask(__name__)

openai.api_key = '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'
bot_token = '6439539582:AAGgYi8oBJnDvrdPnlKoGh6n15Lytq30YKQ'

# MongoDB connection
uri = "mongodb+srv://elliot:kk9999@cluster0.dkrku5w.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['oduraa_db']
user_info_collection = db['users']

# Get the current working directory
current_directory = os.getcwd()

personal_chat_id = '-1002061383128'


# Initialize the bot
bot = telebot.TeleBot(bot_token)

ADMIN_ROLE = "admin"
PRESIDENT_ROLE = "president"
all_levels = ["Level 100", "Level 200", "Level 300", "Level 400", "All"]


# Course feeder feature Code below
#########################################################################################################################################################

bot_name = "Oduraa"
# Conversation states
LEVEL, SEMESTER, COURSE, RESOURCE_TYPE, FEEDBACK = range(5)

# Dictionary to store user data
user_data = {}

# Custom "Back" button
back_button = types.KeyboardButton("Back🔙")

loading_messages = [
    "🚀Please wait while I prepare your resources",
    "🚀Working on it... Just a moment",
    "🚀Getting your resources ready",
] 

# Define the MongoDB collections for each level
local_collections = {}

# Function to update local_collections from the MongoDB database
def update_collections():
    global local_collections

    uri = "mongodb+srv://allen:oduraa_lib_db@cluster0.dkrku5w.mongodb.net/?retryWrites=true&w=majority"
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['oduraa_library']

    # Define the MongoDB collections for each level
    level_collections = {
        "Level 100": db['L100'],
        "Level 200": db['L200'],
        "Level 300": db['L300'],
        "Level 400": db['L400'],
    }

    # Clear the existing local_collections
    local_collections = {}

    # Query each collection and store the documents in local_collections
    for level, collection in level_collections.items():
        documents = list(collection.find())

        # Convert semester values to integers
        for doc in documents:
            doc['semester'] = int(doc['semester'])

        local_collections[level] = documents

    # Print the updated local_collections (for debugging)
    # print(local_collections)
    # json_file_path = 'testt.json'
    # # Save all documents to a JSON file
    # with open(json_file_path, 'w') as json_file:
    #     json.dump(local_collections, json_file, default=str, indent=2)

# Run the update_collections function initially
update_collections()

# Schedule the update every minute
schedule.every(1).minutes.do(update_collections)

# Function to start the schedule in a separate thread
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the schedule in a separate thread
schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.start()


# Courses for each level and semester, may change depending on the work order
level_courses = {
    "Level 100": {
        "First Semester": [
            "Algebra",
            "Applied Electricity",
            "Engineering Technology",
            "Basic Mechanics",
            "Environmental Studies",
            "Technical Drawing",
            "Communication Skills",
        ],
        "Second Semester": [
            "Basic Electronics",
            "Calculus With Analysis",
            "Engineering Research and Technical Report Writing",
            "Introduction to Phsychology",
            "Introduction to Communication Networks",
            "Introduction to Programming_I",
            "Electrical Measurement & Instrumentation",
            "Communication Skills_II",
            "Applied Thermodynamics",
            "Electrical Engineering Drawing",
            "Electrical Machines",
            "Introduction to IT(Matlab)",
        ],
    },
    "Level 200": {
        "First Semester": [
            "Differential Equation",
            "Introduction to Programmin_II",
            "Digital Systems",
            "Analog Communication Systems",
            "Circuit Theory",
            "Engineering In Society",
            "Analog Communication Lab",
            "Basic Accounting_I",
            "Basic Economics_I",
            "French_I",
            "Philosophy_I",
            "Semiconductor Devices",
            "C Programming",
           
        ],
        "Second Semester": [
            "Calculus With Several Variables",
            "Fundamentals of Data Science",
            "Electromagnetic Field Theory",
            "Communication Circuits",
            "Microprocessors",
            "Digital Electronics & Microprocessors Lab",
            "Basic Accounting_II",
            "Basic Economics_II",
            "French_II",
            "Philosophy_II",
            "Digital Systems",
            "Electrical Measurement & Instrumentation",
        ],
    },
    "Level 300": {
        "First Semester": [
            "Random Variables & Stochastic Processes",
            "Numerical Analysis",
            "Information Theory and Coding",
            "Microelectronic Devices & Circuits",
            "Optical Communication",
            "Signals & Systems",
            "Optical Communication Lab",
            "Microprocessors",
            "Statistics",
            "Linear Electronic Circuits",
            
        ],
        "Second Semester": [
            "Computer Networking",
            "Antenna Theory & Design",
            "Communication Systems Lab",
            "Engineering Project Design & Management",
            "Data Communication Principles",
            "Switching Engineering In Communication",
            "Digital Communication Systems",
            "Telecom Infrastructure",
            "Communication Circuits",
        ],
    },
    "Level 400": {
        "First Semester": [
            "Fundamentals of Network Security",
            "Emerging Trends In Communication",
            "Microwave Engineering",
            "Mobile & Wireless Communication",
            "Industrial Placement",
            "Project I",
            "Aviation Communication",
            "Digital Integrated Circuits",
            "VLSI",
            "Computer Application & Projects Design",
            "Electromagnetic Compatibility",
            "Wireless Data Communication Networks",
            "Engineering Economics & Management",
            "Computer Networking",
        ],
        "Second Semester": [
            "Digital Signal Processing",
            "Telecom Policy & Regulation",
            "Satelite Communication & Navigation Systems",
            "Radio Network Planning & Optimization",
            "Enterpreneurship Development",
            "Project II",
            "Radar Communications",
            "Millimeter Wave Technology",
            "Microwave Engineering",
            "Network Planning",
            "Introduction to VLSI"
        ],
    }
}


# Feedback Message
feedback_message = f"🌟 Thanks for using {bot_name} Bot! 🙌 I'm here to assist you, and your feedback is valuable to me. Please type your feedback or any suggestions you have below:Feel free to share your thoughts; I'm here to listen and make your experience even better! 📚🌟"

# Function to create and update the keyboard markup for each state
def update_keyboard_markup(chat_id, state):
    user_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    if state == LEVEL:
        user_markup.row("Level 100", "Level 200")
        user_markup.row("Level 300", "Level 400")
    elif state == SEMESTER:
        user_markup.row("First Semester", "Second Semester")
        user_markup.row(back_button)
    elif state == COURSE:
        selected_level = user_data.get(chat_id, {}).get("level", "")
        selected_semester = user_data.get(chat_id, {}).get("semester", "")
        courses = level_courses.get(selected_level, {}).get(selected_semester, [])
        for course in courses:
            user_markup.row(course)
        user_markup.row(back_button)
    elif state == RESOURCE_TYPE:
        user_markup.row("Past Questions", "Lecture Slides")
        user_markup.row("Recommended Books")
        user_markup.row("Feedback✉️") 
        user_markup.row("Back🔙")
    elif state == FEEDBACK:
        user_markup.row("Back🔙")  
    
    bot.send_message(chat_id, "🌟Choose an option:", reply_markup=user_markup)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    username = message.from_user.first_name

    # Check if the user's chat ID is in the user_info collection
    user_info = user_info_collection.find_one({'chat_id': chat_id})

    if not user_info:
        # If the user is not in the collection, prompt for name and level
        bot.send_message(chat_id, f"👋 Hello {username}! Welcome to {bot_name}, your personal Telecom academic resource assistant. Let's embark on an exciting academic journey. To provide you with a personalized experience, I'd like to know more about you.")
        bot.send_message(chat_id, "📝 What's your full name?")
        user_data[chat_id] = {'state': 'WAITING_FOR_NAME'}
    else:
        # If the user is in the collection, initialize user_data[chat_id] if not present
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        # Set the state to LEVEL to continue the bot like normal
        user_data[chat_id]['state'] = LEVEL

        # Proceed as usual
        user_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_markup.row("Level 100", "Level 200")
        user_markup.row("Level 300", "Level 400")
        bot.send_message(chat_id, f"🎉 Welcome back, {user_info['name']}! Choose your level below.", reply_markup=user_markup)

# Add a new message handler to handle the user's response to the name question
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'WAITING_FOR_NAME')
def process_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text

    # Ask for the user's level
    bot.send_message(chat_id, "📚 What level are you in (e.g., 1 for Level 100)?")
    user_data[chat_id]['state'] = 'WAITING_FOR_LEVEL'

# Add a new message handler to handle the user's response to the level question
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'WAITING_FOR_LEVEL')
def process_level(message):
    chat_id = message.chat.id
    user_data[chat_id]['level'] = message.text

    # Save user information to the user_info collection
    user_info = {
        'chat_id': chat_id,
        'name': user_data[chat_id]['name'],
        'level': user_data[chat_id]['level'],
        'role': 'user'
    }
    user_info_collection.insert_one(user_info)

    channel_invite = "📢To stay connected for latest news and updates, Click the link below to join the channel and be part of the growing community of Telecom Engineers: https://t.me/learn_telesa 🚀📚"
    help_instruction = "Incase of any difficulties or problems encountered type /help."

    # Display welcome message and proceed as usual
    user_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    user_markup.row("Level 100", "Level 200")
    user_markup.row("Level 300", "Level 400")

    bot.send_message(chat_id, f"🎉 Welcome, {user_data[chat_id]['name']}! Choose your level below.", reply_markup=user_markup)
    bot.send_message(chat_id, channel_invite, reply_markup=user_markup)
    bot.send_message(chat_id, help_instruction, reply_markup=user_markup)
    # Reset state to LEVEL
    user_data[chat_id]['state'] = LEVEL
    
@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.chat.id
    help_message = """🤖 Welcome to my Help page 🤖

I'm here to make your academic journey easier. Whether you need course materials, lecture slides, past questions, or books, I've got you covered. No more searching; education is at your fingertips! Here's how I can assist:

1. Start by selecting your level (e.g., Level 100, Level 200) and semester.
2. Choose a course from the available options.
3. Let me know what you need (Past Questions, Lecture Slides, Recommended Books).
4. I'll provide you with the resources you're looking for.

If you have any feedback or questions, feel free to use the 'Feedback✉️' option to get in touch with me. Additionally, you can reach out to Oduraa's Developer(t.me/elliottRannnnns) for clarification, questions, or to report issues.

If you ever encounter any issues, simply type /start to begin a new conversation. Explore my features and access the resources you need for your studies. Enjoy learning! 📚✨
"""
    bot.send_message(chat_id, help_message)
  
@bot.message_handler(commands=['bulk_message'])
def bulk_messages_handler(message):
    chat_id = message.chat.id
    user_info = user_info_collection.find_one({'chat_id': chat_id})

    # Check if the user has the required role to use the command
    if user_info and user_info.get('role') in [ADMIN_ROLE, PRESIDENT_ROLE]:
        # User has the required role

        # Create a keyboard with all levels
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        keyboard.add(*all_levels)

        bot.send_message(chat_id, "Choose the levels you want to send the message/photo to:", reply_markup=keyboard)
        
        # Set the user's state to WAITING_FOR_BULK_LEVEL
        user_data[chat_id] = {'state': 'WAITING_FOR_BULK_LEVEL'}

    else:
        # User doesn't have the required role
        bot.send_message(chat_id, "⚠️ You don't have the required role to use this command.")

# Message handler for users choosing multiple levels for bulk messages
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'WAITING_FOR_BULK_LEVEL')
def bulk_messages_levels_handler(message):
    chat_id = message.chat.id
    selected_levels = message.text.split(",") 

    if 'All' in selected_levels:
        # If 'All' is selected, set all levels in user_data
        user_data[chat_id]['bulk_levels'] = [str(i + 1) for i in range(len(all_levels) - 1)] 
    else:
        # Convert selected levels to numerical representation
        numeric_levels = [str(all_levels.index(level) + 1) for level in selected_levels]
        user_data[chat_id]['bulk_levels'] = numeric_levels

    # Create a keyboard with content options
    content_keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    content_keyboard.row("Photo", "Video")
    content_keyboard.row("Message", "Document")

    bot.send_message(chat_id, "Choose the type of content you want to send:", reply_markup=content_keyboard)

    # Set the user's state to WAITING_FOR_BULK_TYPE
    user_data[chat_id]['state'] = 'WAITING_FOR_BULK_TYPE'

# New function to send bulk content to specified levels
def send_bulk_content(chat_id, content_type, content, levels):
    for level in levels:
        users_with_level = user_info_collection.find({'level': level})
        for user in users_with_level:
            user_chat_id = user['chat_id']
            if content_type == "photo":
                bot.send_photo(user_chat_id, content)
            elif content_type == "video":
                bot.send_video(user_chat_id, content)
            elif content_type == "document":
                bot.send_document(user_chat_id, content)
            elif content_type == "message":
                bot.send_message(user_chat_id, content)
            

# Modified message handler for users choosing the type of content
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == 'WAITING_FOR_BULK_TYPE')
def bulk_messages_type_handler(message):
    chat_id = message.chat.id
    user_info = user_info_collection.find_one({'chat_id': chat_id})

    if user_info and user_info.get('role') in [ADMIN_ROLE, PRESIDENT_ROLE]:
        content_type = message.text.lower()

        # Check if the chosen type is valid
        if content_type not in ["photo", "video", "message", "document"]:
            bot.send_message(chat_id, "⚠️ Invalid option. Please choose 'Photo', 'Video', 'Message', or 'Document'.")
            return

        user_data[chat_id]['bulk_content_type'] = content_type

        # Ask for the content based on the chosen type
        if content_type == "photo":
            bot.send_message(chat_id, "📸 Send the photo you want to send to the selected levels. Please upload the photo directly.")
        elif content_type == "video":
            bot.send_message(chat_id, "🎥 Send the video you want to send to the selected levels. Please upload the video directly.")
        elif content_type == "document":
            bot.send_message(chat_id, "📄 Send the document you want to send to the selected levels. Please upload the document directly.")
        elif content_type == "message":
            bot.send_message(chat_id, "✉️ Enter the message you want to send to the selected levels:")

        # Set the user's state to WAITING_FOR_BULK_CONTENT
        user_data[chat_id]['state'] = 'WAITING_FOR_BULK_CONTENT'
        user_data[chat_id]['bulk_content'] = None  # Initialize bulk_content variable

    else:
        bot.send_message(chat_id, "⚠️ You don't have the required role to use this command.")

    # # Modified message handler for users inputting the message or content
    # @bot.message_handler(func=lambda message: True, content_types=['text', 'video', 'photo', 'document'])
    # def photo_handler(message):
    #     chat_id = message.chat.id
    # if message.content_type == "photo":
    #     if message.photo:
    #         # Extract the largest photo size and get its file_id
    #         media_id = message.photo[-1].file_id
    #         content = media_id
    #         print(f"Photo File ID: {content}")
    #         # Save the content in the user_data for later use
    #         user_data[chat_id]['bulk_content'] = content
            
    #         content_type = user_data[chat_id]['bulk_content_type']
    #         content = user_data[chat_id]['bulk_content']
    #         levels = user_data[chat_id]['bulk_levels']
    #         # Send the content to specified levels
    #         send_bulk_content(chat_id, content_type, content, levels)

    #         # Reset the user's state to None
    #         user_data[chat_id]['state'] = None
    #         user_data[chat_id]['bulk_content_type'] = None
    #         user_data[chat_id]['bulk_content'] = None
    #         user_data[chat_id]['bulk_levels'] = None
    #     else:
    #         bot.send_message(chat_id, "⚠️ Invalid content. Please upload the correct photo.")
    #         return
    # elif message.content_type == "video":
    #     if message.video:
    #         media_id = message.video.file_id
    #         content = media_id
    #         print(f"Video File ID: {content}")
    #         # Save the content in the user_data for later use
    #         user_data[chat_id]['bulk_content'] = content
            
    #         content_type = user_data[chat_id]['bulk_content_type']
    #         content = user_data[chat_id]['bulk_content']
    #         levels = user_data[chat_id]['bulk_levels']
    #         # Send the content to specified levels
    #         send_bulk_content(chat_id, content_type, content, levels)

    #         # Reset the user's state to None
    #         user_data[chat_id]['state'] = None
    #         user_data[chat_id]['bulk_content_type'] = None
    #         user_data[chat_id]['bulk_content'] = None
    #         user_data[chat_id]['bulk_levels'] = None
    #     else:
    #         bot.send_message(chat_id, "⚠️ Invalid content. Please upload the correct video.")
    #         return
    # elif message.content_type == "document":
    #     if message.document:
    #         media_id = message.document.file_id
    #         content = media_id
    #         print(f"Document File ID: {content}")
    #         # Save the content in the user_data for later use
    #         user_data[chat_id]['bulk_content'] = content
        
    #         content_type = user_data[chat_id]['bulk_content_type']
    #         content = user_data[chat_id]['bulk_content']
    #         levels = user_data[chat_id]['bulk_levels']
    #         # Send the content to specified levels
    #         send_bulk_content(chat_id, content_type, content, levels)

    #         # Reset the user's state to None
    #         user_data[chat_id]['state'] = None
    #         user_data[chat_id]['bulk_content_type'] = None
    #         user_data[chat_id]['bulk_content'] = None
    #         user_data[chat_id]['bulk_levels'] = None
    #     else:
    #         bot.send_message(chat_id, "⚠️ Invalid content. Please upload the correct document.")
    #         return
    # elif message.content_type == "text":
    #     content = message.text
    #     print(f"Message: {content}")
    #     # Save the content in the user_data for later use
    #     user_data[chat_id]['bulk_content'] = content

    #     content_type = user_data[chat_id]['bulk_content_type']
    #     content = user_data[chat_id]['bulk_content']
    #     levels = user_data[chat_id]['bulk_levels']
    #     # Send the content to specified levels
    #     send_bulk_content(chat_id, content_type, content, levels)

    #     # Reset the user's state to None
    #     user_data[chat_id]['state'] = None
    #     user_data[chat_id]['bulk_content_type'] = None
    #     user_data[chat_id]['bulk_content'] = None
    #     user_data[chat_id]['bulk_levels'] = None

        
@bot.message_handler(func=lambda message: message.text in ["Level 100", "Level 200", "Level 300", "Level 400"])
def level(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['level'] = message.text
        user_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_markup.row("First Semester", "Second Semester")
        user_markup.row(back_button)
        bot.send_message(chat_id, f"You selected {message.text}. Choose a semester:", reply_markup=user_markup)
        user_data[chat_id]['state'] = SEMESTER
    else:
        bot.send_message(chat_id, "Please start the conversation.")
        start(message)

@bot.message_handler(func=lambda message: message.text in ["First Semester", "Second Semester"])
def semester(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['semester'] = message.text
        user_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

        # Get the available courses based on the selected level and semester
        selected_level = user_data[chat_id]['level']
        selected_semester = user_data[chat_id]['semester']
        courses = level_courses.get(selected_level, {}).get(selected_semester, [])

        for course in courses:
            user_markup.row(course)

        user_markup.row(back_button)
        bot.send_message(chat_id, f"You selected {message.text}. Choose a course:", reply_markup=user_markup)
        user_data[chat_id]['state'] = COURSE
    else:
        bot.send_message(chat_id, "Please start the conversation.")
        start(message)

@bot.message_handler(func=lambda message: message.text in level_courses.get(user_data.get(message.chat.id, {}).get('level', ''), {}).get(user_data.get(message.chat.id, {}).get('semester', ''), []))
def course(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['course'] = message.text
        user_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_markup.row("Past Questions", "Lecture Slides")
        user_markup.row("Recommended Books")
        user_markup.row("Feedback✉️")
        user_markup.row("Back🔙")
        bot.send_message(chat_id, f"You selected {message.text}. Choose a resource type:", reply_markup=user_markup)
        user_data[chat_id]['state'] = RESOURCE_TYPE
    else:
        bot.send_message(chat_id, "Please start the conversation.")
        start(message)

# Update the resource_type function to call send_files_from_mongodb
@bot.message_handler(func=lambda message: message.text in ["Past Questions", "Lecture Slides", "Recommended Books"])
def resource_type(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['resource_type'] = message.text

        # Construct the query based on the user's selections
        selected_level = user_data[chat_id]['level']
        selected_semester = user_data[chat_id]['semester']
        selected_course = user_data[chat_id]['course']
        selected_resource_type = message.text

        # Query the MongoDB collection for relevant documents
        query = {
            'semester': 1 if selected_semester == 'First Semester' else 2,
            'course': selected_course,
            'type': selected_resource_type,
        }

        # Use the appropriate local collection based on the selected level
        if selected_level in local_collections:
          collection = local_collections[selected_level]
          # Perform an in-memory filter to simulate querying
          documents = [doc for doc in collection if all(doc[key] == query[key] for key in query)]
          # Send the first batch of documents
          send_files_from_mongodb(chat_id, documents)
        else:
          # Handle the case where the selected level is not found
          print(f"Collection for {selected_level} not found.")
      

        
        # Update the keyboard markup to the RESOURCE_TYPE state
        update_keyboard_markup(chat_id, RESOURCE_TYPE)
    else:
        bot.send_message(chat_id, "Please start the conversation.")
        start(message)

# Keep track of the message IDs for each batch
batch_messages = {}

def send_files_from_mongodb(chat_id, documents, start_index=0):
    if documents:
        batch_size = 10
        total_documents = len(documents)
        end_index = min(start_index + batch_size, total_documents)

        document_messages = []

        for i in range(start_index, end_index):
            document = documents[i]
            topic = document.get('topic', 'N/A')
            description = document.get('description', 'N/A')

            # Add each document with a number to the message
            document_message = f"{i + 1}. Topic: {topic}\nDescription: {description}"
            document_messages.append(document_message)

        # Create a single message with all documents
        full_message = "\n\n".join(document_messages)

        # Create the keyboard with buttons for each document number
        keyboard = InlineKeyboardMarkup()

        row_buttons = []
        for i in range(start_index, end_index):
            url_button = InlineKeyboardButton(str(i + 1), callback_data=f"document_{i}")
            row_buttons.append(url_button)

            # Make the number of buttons per row to 5 to make the buttons sizable
            if len(row_buttons) == 5:
                keyboard.row(*row_buttons)
                row_buttons = []

        # Add the last row of buttons
        if row_buttons:
            keyboard.row(*row_buttons)

        # Add "Next" and "Previous" buttons
        if end_index < total_documents:
            next_button = InlineKeyboardButton("Next", callback_data=f"next_{end_index}")
            keyboard.row(next_button)

        if start_index >= batch_size:
            # Add "Previous" button if there are more than 10 documents before
            previous_button = InlineKeyboardButton("Previous", callback_data=f"previous_{start_index - batch_size}")
            keyboard.row(previous_button)

        # Delete the previous batch's message if it exists
        previous_message_id = batch_messages.get(chat_id)
        if previous_message_id:
            try:
                bot.delete_message(chat_id, previous_message_id)
            except Exception as e:
                print(f"Error deleting message: {e}")

        # Send the full message with documents and buttons
        new_message = bot.send_message(chat_id, full_message, reply_markup=keyboard)

        # Update the batch_messages dictionary with the new message ID
        batch_messages[chat_id] = new_message.message_id
    else:
        bot.send_message(chat_id, "I'm sorry, but I couldn't find any files for the selected resource type. If you have any other questions or need assistance with something else, feel free to ask. I'm here to help!")



# Handle callback queries for document buttons
@bot.callback_query_handler(func=lambda call: call.data.startswith("document"))
def handle_document_button(call):
    chat_id = call.message.chat.id

    # Extract the document index from the callback data
    document_index = int(call.data.split("_")[1])

     # Query the database again starting from the next batch
    selected_level = user_data[chat_id]['level']
    selected_semester = user_data[chat_id]['semester']
    selected_course = user_data[chat_id]['course']
    selected_resource_type = user_data[chat_id]['resource_type']

    # Construct the query based on the user's selections
    query = {
        'semester': 1 if selected_semester == 'First Semester' else 2,
        'course': selected_course,
        'type': selected_resource_type,
    }

# Use the appropriate local collection based on the selected level
    if selected_level in local_collections:
          collection = local_collections[selected_level]
          # Perform an in-memory filter to simulate querying
          documents = [doc for doc in collection if all(doc[key] == query[key] for key in query)]
          # Send the first batch of documents
          send_files_from_mongodb(chat_id, documents)
    else:
          # Handle the case where the selected level is not found
          print(f"Collection for {selected_level} not found.")
    
    # Get the link of the selected document
    selected_document = documents[document_index]
    document_link = selected_document.get('link', '')
    #Convert the document link to string first and then pass the string to telegram to send the file
    document_str = str(document_link)
    bot.send_document(chat_id, document_str)



# Handle callback queries for "Next" and "Previous" buttons
@bot.callback_query_handler(func=lambda call: call.data.startswith("next") or call.data.startswith("previous"))
def handle_navigation_buttons(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Extract the action and start_index from the callback data
    action, start_index = call.data.split("_", 1)
    start_index = int(start_index)

    # Query the database again starting from the next/previous batch
    selected_level = user_data[chat_id]['level']
    selected_semester = user_data[chat_id]['semester']
    selected_course = user_data[chat_id]['course']
    selected_resource_type = user_data[chat_id]['resource_type']

    # Construct the query based on the user's selections
    query = {
        'semester': 1 if selected_semester == 'First Semester' else 2,
        'course': selected_course,
        'type': selected_resource_type,
    }

    # Use the appropriate local collection based on the selected level
    if selected_level in local_collections:
          collection = local_collections[selected_level]
          # Perform an in-memory filter to simulate querying
          documents = [doc for doc in collection if all(doc[key] == query[key] for key in query)]
          # Send the batch of documents
          send_files_from_mongodb(chat_id, documents, start_index)
    else:
          # Handle the case where the selected level is not found
          print(f"Collection for {selected_level} not found.")
    

    # Clear the inline keyboard markup
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)


# Handler for the "Back" button
@bot.message_handler(func=lambda message: message.text == "Back🔙", content_types=['text'])
def back(message):
    chat_id = message.chat.id
    current_state = user_data.get(chat_id, {}).get('state', None)
    
    if current_state is not None:
        if current_state == RESOURCE_TYPE:
            # Go back to the course selection
            user_data[chat_id]['state'] = COURSE
            update_keyboard_markup(chat_id, COURSE)
        elif current_state == COURSE:
            # Go back to the semester selection
            user_data[chat_id]['state'] = SEMESTER
            update_keyboard_markup(chat_id, SEMESTER)
        elif current_state == SEMESTER:
            # Go back to the level selection
            user_data[chat_id]['state'] = LEVEL
            update_keyboard_markup(chat_id, LEVEL)
        elif current_state == FEEDBACK:
            # Go back to the RESOURCE_TYPE state
            user_data[chat_id]['state'] = RESOURCE_TYPE
            update_keyboard_markup(chat_id, RESOURCE_TYPE)
    else:
        bot.send_message(chat_id, "Please start the conversation.")
        start(message)


# Handler for the "Feedback" button
@bot.message_handler(func=lambda message: message.text == "Feedback✉️", content_types=['text'])
def feedback(message):
    chat_id = message.chat.id

    # Make sure the user's chat ID exists in user_data
    if chat_id in user_data:
        bot.send_message(chat_id, feedback_message)
        user_data[chat_id]['state'] = FEEDBACK
    else:
        bot.send_message(chat_id, "Please start the conversation.")
        start(message)


@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == FEEDBACK)
def process_feedback(message):
    chat_id = message.chat.id
    user_feedback = message.text
    
    username = message.from_user.username
    
    # Send user feedback to the feedback channel
    bot.send_message(personal_chat_id, f"Feedback from user @{username}:\n\n{user_feedback}")
    
    # Send a thank you message
    bot.send_message(chat_id, "🤖 I appreciate your feedback! 🙌\nI value your input; it helps me improve and serve you better. If you have more to share or any questions, don't hesitate to reach out anytime. Your experience matters to me! 📚✨")
    
    # move back to the RESOURCE_TYPE state
    user_data[chat_id]['state'] = RESOURCE_TYPE
    update_keyboard_markup(chat_id, RESOURCE_TYPE)


# LLM Input feature Code below
#########################################################################################################################################################

@bot.message_handler(func=lambda message: True, content_types=['text', 'voice', 'photo'])
def handle_user_message(message):
    chat_id = message.chat.id
# Check if the user has a previous audio message and delete it
    if 'audio_message_id' in user_data[chat_id]:
        try:
            bot.delete_message(chat_id, user_data[chat_id]['audio_message_id'])
        except Exception as e:
            print(f"Error deleting audio message, No previous audio foound: {e}")

    if message.content_type == 'text':
        # For text messages, directly send to GPT for a response
        response_text = interact_with_assistant(chat_id, message.text)
        send_response_with_buttons(chat_id, response_text)

    elif message.content_type == 'voice':
        # For audio messages, transcribe to text and then send to GPT
        print("Audio received")
        # Get the file ID of the voice note
        file_id = message.voice.file_id

        # Download the voice note file
        voice_file_info = bot.get_file(file_id)
        voice_file = bot.download_file(voice_file_info.file_path)

        # Convert the voice note to WAV format
        audio_data = AudioSegment.from_file(io.BytesIO(voice_file), format="ogg")
        audio_data.export("voice_note.wav", format="wav")

        # Transcribe the voice note
        text = transcribe_audio('voice_note.wav')

        response_text = interact_with_assistant(chat_id, text)
        send_response_with_buttons(chat_id, response_text)

    # elif message.content_type == 'photo':
    #     print("Photo Received")
        
    #  # Get the file ID of the photo
    # file_id = message.photo[-1].file_id

    # # Get the file path using the file ID
    # file_info = bot.get_file(file_id)
    # file_path = file_info.file_path

    # # Download the photo as bytes
    # file_data = bot.download_file(file_path)

    #  # Send a confirmation message
    # bot.reply_to(message, 'Image received and processing...')

    # # Pass the downloaded photo data to the processImage function
    # photomath_api(chat_id, file_data)


# Function to transcribe audio
def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"Transcribed text: {text}")
        return text
    except sr.UnknownValueError:
        return "Sorry, could not understand audio."
    except sr.RequestError as e:
        return "Error with the request; {0}".format(e)



# LLM Integration feature Code below
#########################################################################################################################################################

# Function to interact with the AI assistant when an inout is sent to the chat
def interact_with_assistant(chat_id, user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are Oduraa, a telecom academic resource assistant built in honor of the late Alberta Oduraa Quartey, a former teaching assistant in the department of Telecommunications Engineering, KNUST. You specialize in delivering course materials to users based on their selections. Users can choose their academic level, semester, course, and resource type, including options like past questions, recommended books, or lecture slides, and you provide the relevant materials. All these selections are made from the buttons available in the bot chat so you direct user to the bot help to learn how to get resources. Users can access the bot help by typing '/help' in the chat. Additionally, you have the ability to respond to text messages and offer assistance when user prompts telecom-related questions, research, and topics mostly provide detailed responses for great user experience. You were built by EDULINE AI Labs, a division in RAIDTECH EDULINE,  a company aimed at revolutionizing educational accessibility in Ghana.The team that built you are Elliot Amponsah and Allen Selasie Korbla Ametame along with some students in the telecom departement who helped build a robust digital library for the bot to reference resources from(Asare Ansah Prince, Akuaku Kabu Joseph, Rocklyn Bioh, Emmanuella Amankwah-Fobi, Godfred Addo, Richard Agyei, Juliet Osei Bonsu and some first years(Phoebe, Emmanuel Okine and Spendylove)"},
                {"role": "user", "content": user_input},
            ],
        )

        # Get the assistant's reply
        assistant_reply = response['choices'][0]['message']['content']

        return assistant_reply

    except Exception as e:
        print(f"Error interacting with assistant: {e}")
        bot.send_message(chat_id, "I'm sorry, but I encountered an error while processing your request. Please try again later.")


def photomath_api(chat_id, image_data):
    url = "https://photomath1.p.rapidapi.com/maths/solve-problem"

    files = {"image": ('photo.jpg', image_data, 'image/jpeg')}
    payload = {"locale": "en"}
    headers = {
        "X-RapidAPI-Key": "4c5ab120f5msh39abf03a106144ap1b5e29jsn3b5774fc444d",
        "X-RapidAPI-Host": "photomath1.p.rapidapi.com"
    }

    response = requests.post(url, data=payload, files=files, headers=headers)

    # Parse the JSON response
    result_json = json.loads(response.text)

    # Print the JSON structure (optional)
    print(json.dumps(result_json, indent=2))
    bot.send_message(chat_id, json.dumps(result_json, indent=2))

    # Extract the answer from the JSON dynamically
    try:
        answer = extract_answer(result_json)
        # Send the answer back to the chat
        bot.send_message(chat_id, f'The answer is: {answer}')
    except KeyError:
        # Handle the case when the structure is not as expected
        bot.send_message(chat_id, 'Unable to extract the answer. Please try again.')

# Function to recursively search for the answer in the JSON structure
def extract_answer(data):
    if isinstance(data, list):
        for item in data:
            result = extract_answer(item)
            if result is not None:
                return result
    elif isinstance(data, dict):
        if "value" in data:
            return data["value"]
        elif "children" in data and isinstance(data["children"], list):
            for child in data["children"]:
                result = extract_answer(child)
                if result is not None:
                    return result
    return None




# LLM Response feature Code below
#########################################################################################################################################################

def send_response_with_buttons(chat_id, response_text):
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    read_aloud_button = types.InlineKeyboardButton("Read Aloud🔊", callback_data="read_aloud")
    no_thanks_button = types.InlineKeyboardButton("No Thanks🙅‍♂️", callback_data="no_thanks")
    inline_markup.add(read_aloud_button, no_thanks_button)

    # Send the response with inline buttons
    bot.send_message(chat_id, response_text, reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_button_press(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Handle button presses
    if call.data == "read_aloud":
        # Read the response aloud using playHT's api
        response_text = call.message.text
        read_aloud_with_playHT(chat_id, response_text)
    elif call.data == "no_thanks":
        pass

    # Clear the inline keyboard markup
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)

# Function to read aloud with the PlayHT API
def read_aloud_with_playHT(chat_id, text):
    try:
            url = "https://api.play.ht/api/v2/tts"

            payload = {
        "text": text,
        "voice": "s3://voice-cloning-zero-shot/d72f2993-9529-4b19-a22a-9e00ba6e993d/enhanced/manifest.json",
        "output_format": "mp3",
        "voice_engine": "PlayHT2.0",
        "speed": "0.8"
        }
            headers = {
        "accept": "text/event-stream",
        "content-type": "application/json",
        "AUTHORIZATION": "d8f4b440020c4572a811c877ee1c723e",
        "X-USER-ID": "pUgv7iuQchQvIVnWbVgRvlt2Ufb2"
        }

            response = requests.post(url, json=payload, headers=headers, stream=True)

            responseInText = response.text
            print(responseInText)

            # Use regex to extract the URL
            url_pattern = re.compile(r'"url":"(https://[^"]+)"')
            match = url_pattern.search(responseInText)

            # Check if a match is found
            if match:
                extracted_url = match.group(1)

                # Download the file
                file_name = "Oduraa-speaking.mp3"
                with open(file_name, 'wb') as file:
                    file.write(requests.get(extracted_url).content)

                # Send the file to the bot
                with open(file_name, 'rb') as audio_file:
                    sent_message = bot.send_audio(chat_id, audio_file)

                # Delete the downloaded file
                os.remove(file_name)
                 # Get the message ID of the sent audio message
                audio_message_id = sent_message.message_id

                # Save the message ID in user_data: this help to keep track and know if there is existing audio in the chat
                user_data[chat_id]['audio_message_id'] = audio_message_id
            else:
                print("No URL found in the text.")
    except Exception as e:
        print(f"Error sending or deleting audio message: {e}")

# Function to read aloud with the PlayHT API
def read_aloud_with_gTTS(chat_id, text):
    try:

        tts = gTTS(text=text, lang='en', slow=False)

        # Save the speech as an audio file
        audio_file_path = "read_aloud.mp3"
        tts.save(audio_file_path)

        # Send the audio file to the user
        with open(audio_file_path, 'rb') as audio_file:
            sent_message = bot.send_audio(chat_id, audio_file)

        # Remove the temporary audio file
        os.remove(audio_file_path)

        # Get the message ID of the sent audio message
        audio_message_id = sent_message.message_id

        # Save the message ID in user_data
        user_data[chat_id]['audio_message_id'] = audio_message_id

    except Exception as e:
        print(f"Error sending or deleting audio message: {e}")        
    
        
# Webhook route definition
@app.route('/' + bot_token, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200      


# Code to run the bot below
#########################################################################################################################################################

WEBHOOK_URL = 'https://oduraa-bot-9c5d3251e8b1.herokuapp.com/'  

# Set the webhook for the bot
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL + '/' + bot_token)

if __name__ == '__main__':

    # Run the Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    