Course: CS 305 - Operating Systems
Assignment: Process Scheduling Simulator
Student: Melek Arslan
ID: 220446018
-------------------------------------------

About the Project:
hi, this is my implementation for the cpu scheduling assignment.
i wrote the code in python3. it reads the input file and simulates these algorithms:
1. FCFS (First-Come First-Served)
2. SJF (Shortest Job First - Non-preemptive)
3. Round Robin (RR - Preemptive)
4. Priority Scheduling (Non-preemptive)

How to Run:
you don't need any external libraries, just standard python 3.
open your terminal in this folder and run these commands:

1. to run with the sample input (default time quantum = 3 for RR):
   python scheduler.py processes.txt

2. if you want to change the time quantum for RR (example: 4):
   python scheduler.py processes.txt 4

3. to see the starvation problem i discussed in the report:
   python scheduler.py starvation.txt

Files:
- scheduler.py: main source code.
- processes.txt: the example input from the assignment description.
- starvation.txt: my custom input file to show starvation.
- README.txt: this file.