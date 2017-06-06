import praw
import sys
import csv
import os
import time

def bot():
    reddit = praw.Reddit('gradebot')

	# checks if csv file is present and errors if it isnt
    if not os.path.isfile("grade_data.csv"):
        #print("Data not present")
        sys.exit("Data not present")
		
    else:
        with open("grade_data.csv") as csvfile:
            csv_read = csv.reader(csvfile)
            grade_data = []
            header = []
            table = []
            rownum = 0

            for row in csv_read:
                if rownum == 0:
                    header = row
                    for word in row:
                        table.append(":-:")
                else:
                    grade_data.append(row)
                
                rownum += 1
        
	# check if "comments_replied_to.txt" exists
    if not os.path.isfile("comments_replied_to.txt"):
        comments_replied_to = []

	# if file exists, loads the list of comments responded to so far
    else:
        with open("comments_replied_to.txt","r") as f:
            comments_replied_to = f.read()
            comments_replied_to = comments_replied_to.split("\n")
            comments_replied_to = list(filter(None, comments_replied_to))
    
    # Checks if the post has been responded to (for checking title and self text)
    if not os.path.isfile("posts_replied_to.txt"):
        posts_replied_to = []
        
    else:
        with open("posts_replied_to.txt","r") as p:
            posts_replied_to = p.read()
            posts_replied_to = posts_replied_to.split("\n")
            posts_replied_to = list(filter(None, posts_replied_to))
            
    subreddit = reddit.subreddit("ClimbingGradeBot+Climbing") # chooses what subreddits the bot can respond to

    comment_list = [] # declares a list for the comment that will be posted by the bot
    source_text = " " # declares a string which will contain the text to be checked for a grade
       
    for comment in subreddit.stream.comments():
        comment.refresh()
        submission = comment._submission
        if "!gradebot" in comment.body and comment.id not in comments_replied_to and submission.id not in posts_replied_to: # Checks for call for bot
            if comment.is_root: # Determines if the bot is the parent comment
                # This will check the title for a grade
                source_text = comment.link_title
                posts_replied_to.append(submission.id)
            else:
                # This will check the parent comment for a grade
                parent_comment = comment.parent()
                parent_comment.refresh() # Gets info for the parent comment
                parent_author = parent_comment.author # Gets the author of the parent comment 
                if parent_author.name != "ClimbingGradeBot": # Checks the bot isnt being called on itself
                   source_text = parent_comment.body
            
            # Runs the functions for finding the grade and making the comment
            comment_list = find_grade(source_text, grade_data, header, table) # Finds the grade in source_text and appends header etc. if required
            # Checks the self post text for a grade, only if the title didn't return a grade
            if len(comment_list) == 0 and comment.is_root: 
                source_text = submission.selftext
                comment_list = find_grade(source_text, grade_data, header, table) # Finds the grade in source_text and appends header etc. if required
                posts_replied_to.append(submission.id)
            
            comment_writer(comment, comment_list) # Writes the comment
            comments_replied_to.append(comment.id) # adds the comment id to the list of comments replied to so the bot doesnt loop
        # writes the comment ids to the text file so that if the bot is restarted the same commments cant be responded to
        with open("comments_replied_to.txt", "w") as f:
            for comment_id in comments_replied_to:
                f.write(comment_id + "\n")
        
        # Writes post ids to the text file so if bot restarts the same posts aren't responded to and also stops the funky blank source_text error
        with open("posts_replied_to.txt","w") as p:
            for post_id in posts_replied_to:
                p.write(post_id + "\n")
            
    return
# Function that searches the relevant text for a grade and develops the correct string response
def find_grade(source_text, grade_text, header, table):
    positive_result_counter = 0 # Counts how many positive results are detected by the bot
    comment_list = []
    # Searches each entry from the csv file to see if any of them are identical to a word in the title
    for row in grade_text:
        for i, grade in enumerate(row):
            for word in source_text.split():
                if word == grade:
                    row[i] = "**" + word + "**" # Replaces the matched grade with a bolded version
                    positive_result_counter += 1 # Adds a count to the positive results
                    comment_list.append(row) 
    if positive_result_counter >= 1:
        comment_list.insert(0,table) # inserts the dashes required for reddit tables before the grades
        comment_list.insert(0,header) # inserts the titles of each column before the grades and dashes
    
    return comment_list

# Function that formats and writes the comment as a reply to the call for the bot
def comment_writer(comment, comment_list):
    comment_formatted = " "
    if len(comment_list) > 0: # Checks if there has been an entry into the list (if not this means there was no grade detected or there was an error somewhere)
        for row in comment_list:
            comment_formatted += " | ".join(row) + "\n" # Changes the row into a string with each entry in the list separated by | 
    else:
        comment_formatted = "No grade detected." # If there is no entry into the list then this is the response given
    comment_formatted += "\n"
    comment_formatted += "--- \n"
    comment_formatted += "[Wiki](https://www.reddit.com/r/ClimbingGradeBot/wiki/index) | [Report Bug](https://www.reddit.com/message/compose?to=%2Fr%2FClimbingGradeBot)"
    comment.reply(comment_formatted) # posts a comment reply to the !gradebot call with text defined by comment_string and formatted in this function
    return

bot()
