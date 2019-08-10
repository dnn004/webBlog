# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import jinja2
import webapp2

import hmac

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

SECRET = "azoyus"

class Blog(db.Model):
	subject = db.StringProperty(required = True)
	blog = db.TextProperty(required = True)
	user = db.StringProperty(required = True)
	post_id = db.IntegerProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	date = db.DateProperty(auto_now_add = True)
	points = db.IntegerProperty(required = True)

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class Comment(db.Model):
	body = db.TextProperty(required = True)
	username = db.StringProperty(required = True)
	postID = db.IntegerProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class Voted(db.Model):
	username = db.StringProperty(required = True)
	postID = db.IntegerProperty(required = True)
	value = db.StringProperty(required = True)
	voteID = db.IntegerProperty(required = True)

def hash_str(s):
	return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
	return "%s" %  hash_str(s)

def check_secure_val(h, inPut):
	if h == make_secure_val(inPut):
		return True
	else:
		return False

def check_user(name, pw):
	user_account_name = None
	user_account_password = None

	users = db.GqlQuery("SELECT * FROM User ")
	for user in users:
		if name == user.username:
			user_account_name = user.username
			user_account_password = user.password

	if user_account_name != None:
		if check_secure_val(user_account_password, pw):
			return "True"
		else: 
			return "Wrong password"
	else:
		return "Username doesn't exist"

# Basic functions for handling classes, taken from Udacity
class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a,**kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

# Shows all posts in a main page
class MainBlogPage(Handler):
	def handleAllPost(self):
		blogs = db.GqlQuery("SELECT * FROM Blog "
							"ORDER BY created DESC ")
		loggedin_cookie_val = self.request.cookies.get("loggedin")
		username_cookie_val = self.request.cookies.get("username")
		self.render("all_post.html", blogs=blogs, logged_in=loggedin_cookie_val, current_user=username_cookie_val)
	
	def get(self):
		self.handleAllPost()

# Type in a new post
class NewPostHandler(Handler):

	def handleNewPost(self, subject="", blog="", error=""):
		self.render("new_post.html", subject=subject, blog=blog, error=error)

	def get(self):
		self.handleNewPost()

	def post(self):
		subject = self.request.get("subject")
		blog = self.request.get("blog")
		username_cookie_val = ""
		post_id = 0

		#Check if both subject and blog content are typed in
		if subject and blog:

			loggedin_cookie_val = self.request.cookies.get("loggedin")
		
			if loggedin_cookie_val == "true":
				username_cookie_val = self.request.cookies.get("username")
			else:
				username_cookie_val = "Anonymous"

			post = Blog(subject = subject, blog = blog, user=username_cookie_val, post_id=0, points=0)
			post.put()
			new_post_id = post.key().id()
			post.post_id = new_post_id
			post.put()
			
			#Redirect to a permalink with only the newly entered blog
			self.redirect_to("post", post_id=new_post_id)

		else:
			error = "Please have both subject and blog content"
			self.handleNewPost(subject, blog, error)

# View a post and its comments
class PostHandler(Handler):

	def renderPost(self, post_id="", error=""):
		int_post_id = int(post_id)
		username_cookie_val = str(self.request.cookies.get("username"))
		# Select the comments that have the postID the same as the post to be rendered
		comments = db.GqlQuery("SELECT * FROM Comment "
								"WHERE postID = %s " %int_post_id
								+ "ORDER BY created ASC")

		# Just a blog list containing one blog ASK!
		blogs = db.GqlQuery("SELECT * FROM Blog "
							"WHERE post_id = %s " %int_post_id)

		votes = db.GqlQuery("SELECT * FROM Voted "
							# "WHERE username = '%s'" %username_cookie_val)
							"WHERE postID = %d AND username = '%s'" %(int_post_id, username_cookie_val))
							# "WHERE postID = '5066549580791808' AND username = '18dnguyen32'")

		loggedin_cookie_val = self.request.cookies.get("loggedin")
		self.render("post.html", username=username_cookie_val, comments=comments, blogs=blogs, votes=votes, post_id=post_id, logged_in=loggedin_cookie_val, error=error)

	def get(self, post_id):
		print('PRINTED')
		int_post_id = int(post_id)
		a_post = Blog.get_by_id(int_post_id)
		self.renderPost(post_id)


	def post(self, post_id):
		int_post_id = int(post_id)

		comment_text = self.request.get("comment")
		upvote = self.request.get("upvote")
		downvote = self.request.get("downvote")
		username_cookie_val = self.request.cookies.get("username")

		if comment_text:
				comment = Comment(body = comment_text, username = username_cookie_val, postID = int_post_id)
				comment.put()
				self.renderPost(int_post_id)
				time.sleep(0.3)
				self.redirect_to("post", post_id=int_post_id)
		else:
			error = "Empty comment"
			self.renderPost(int_post_id, error)

		a_post = Blog.get_by_id(int_post_id)

		# vote = db.GqlQuery("SELECT * FROM Voted "
		# 					"WHERE postID = %d AND username = '%s'" %(int_post_id, username_cookie_val))


		# if !voted

		# voted = Voted(username = username_cookie_val,  postID = int_post_id, value="none", voteID="0")

		# if upvote:
		# 	a_post.points = a_post.points + 1
		# 	# voted = Voted(username = username_cookie_val,  postID = int_post_id, value="up", voteID="0")
		# 	voted.value = "up"
		# 	voted.put()
		# 	new_vote_id = voted.key().id
		# 	voted.voteID = new_vote_id
		# 	voted.put()

		# elif downvote:
		# 	a_post.points = a_post.points - 1
		# 	# voted = Voted(username = username_cookie_val,  postID = int_post_id, value="down", voteID="0")
		# 	voted.value = "down"
		# 	voted.put()
		# 	new_vote_id = voted.key().id
		# 	voted.voteID = new_vote_id
		# 	voted.put()

		# self.response.set_cookie("vote", "voted")
		a_post.put()
		self.redirect_to("post", post_id=int_post_id)

# Allows the user to edit one's own post
class EditHandler(Handler):

	def handleEditPost(self, subject="", blog="", error=""):
		self.render("edit.html", subject=subject, blog=blog, error=error)

 	def get(self, post_id):
 		a_post = Blog.get_by_id(int(post_id))
 		self.handleEditPost(subject=a_post.subject, blog=a_post.blog)

 	def post(self, post_id):

 		subject = self.request.get("subject")
		blog = self.request.get("blog")
		delete = self.request.get("delete")

		# Check if a delete request has been receieved
		if delete:
			a_post = Blog.get_by_id(int(post_id))
			a_post.delete()
			time.sleep(0.3)
			self.redirect("/blog")

		# Check if both subject and blog content are typed in
		elif subject and blog:

			a_post = Blog.get_by_id(int(post_id))

			a_post.subject = subject
			a_post.blog = blog
			a_post.put()
			
			#Redirect to a permalink with only the newly entered blog
			self.redirect_to("post", post_id=post_id)

		else:
			error = "Please have both subject and blog content"
			self.handleEditPost(subject, blog, error)

# Allows the user to sign up with an account
class RegistrationHandler(Handler):

	def handleRegistration(self, username="", error=""):
		users = db.GqlQuery("SELECT * FROM User "
							"ORDER BY created DESC ")
		self.render("registration.html", username=username, users=users, error=error)

	def get(self):
		self.handleRegistration()

	def post(self):
		users = db.GqlQuery("SELECT * FROM User "
							"ORDER BY created DESC ")

		username = self.request.get("username")
		password = self.request.get("password")

		if username and password:

			# Check if username already exists
			for user in users:
				if user.username == username:
					error = "Username already existed"
					self.handleRegistration(username, error)
					return

			#if username exists, enters it into the database
			encrypted_password = make_secure_val(password)
			userInfo = User(username = username, password = encrypted_password)
			userInfo.put()

			# self.response.headers.add_header('Set-Cookie', str('username=%s' % username))
			self.response.set_cookie("username", username)
			self.response.set_cookie("loggedin", "true")

			self.redirect_to("welcome", username=username)

		else:
			error = "Please have both username and password"
			self.handleRegistration(username, error)

# Shows a welcome message to a new user
class WelcomeHandler(Handler):
	def handleWelcome(self, username=""):
		self.render("welcome.html", username=username)

	def get(self, username):
		username_cookie_val = self.request.cookies.get("username")

		# Handle welcome access without cookie
		if username_cookie_val == username:
			self.handleWelcome(username_cookie_val)
		else:
			self.redirect("/blog/registration")

# Allows the user to login into an existing account
class LoginHandler(Handler):
	def LoginHandler(self, username="", error=""):
		self.render("login.html", username=username, error=error)

	def get(self):
		self.LoginHandler()

	def post(self):
		username_input = self.request.get("username")
		password_input = self.request.get("password")

		if username_input and password_input:
			check_return = check_user(username_input, password_input)
			if check_return == "True":
				# Set the cookies for the current user and the loggedin status
				self.response.set_cookie("username", username_input)
				self.response.set_cookie("loggedin", "true")
				self.redirect_to("welcome", username=username_input)
			else:
				error = check_return
				self.LoginHandler(username_input, error)
		else:
			error = "Please have both username and password"
			self.LoginHandler(username_input, error)

# Allows the user to sign out
class LogoutHandler(Handler):
	def get(self):
		self.response.delete_cookie("username")
		self.response.set_cookie("loggedin", "false")
		self.redirect("/blog/registration")

app = webapp2.WSGIApplication([
							   webapp2.Route("/blog", handler=MainBlogPage, name="home"),
						       webapp2.Route("/blog/newpost", handler=NewPostHandler, name="newpost"),
						       webapp2.Route("/blog/registration", handler=RegistrationHandler, name="registration"),
						       webapp2.Route("/blog/login", handler=LoginHandler, name="login"),
						       webapp2.Route("/blog/edit/<post_id>", handler=EditHandler, name="edit"),
						       webapp2.Route("/blog/logout", handler=LogoutHandler, name="logout"),
						       webapp2.Route("/blog/registration/welcome/<username>", handler=WelcomeHandler, name="welcome"),
						       webapp2.Route("/blog/<post_id>", handler=PostHandler, name="post")
						      ], 
							  debug=True)
