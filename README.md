[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/QwFWBwI4)

# Activity Regognition

## Setup
1. Clone the repo and navigate to it via `cd assignment-03-activity-recognition-pink`.
2. Set it up a virtual enviroment running `python -m venv .venv`.
3. Activate the virtual environment using `.venv\Scripts\activate` on Windows and `source .venv/bin/activate` on Linux/Mac.
4. Install the required dependencies via `pip install -r requirements.txt`.

### Data Gathering
Make sure your DIPPID device is connected to the same network as the host device. The program will prompt you to press Button 1 before each session.

To start the gathering data , run `python gather_data.py`.

### Fitness Trainer App
To start the app, run `python fitness_trainer.py`.


# Documentation of the ML Process
Recordings from the [shared repo](https://github.com/ITT-26/assignment-03-data-collection) were used for training and evaluating a SVM.

## File name cleanup
- unified activity names: `jumping_jacks` to `jumpingjacks` (ferdi, lennart, patrick, vanessa)
- converted index to start at 1 (ferdi, vanessa)
- replaced full name with one lowercase word (daniel, georg, thu)
- lowercased all filename segments (vanessa) 
