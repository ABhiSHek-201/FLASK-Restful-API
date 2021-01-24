from flask import Flask, request, jsonify
from flask_restful import Resource, Api,reqparse,fields,marshal_with,abort
from flask_sqlalchemy import SQLAlchemy
import json
import werkzeug
# with open("config.json",'r') as c:
#     params=json.load(c)['params']

app=Flask(__name__)
api=Api(app)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'
# app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/prac_task'
db=SQLAlchemy(app)

class users(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	uname=db.Column(db.String(50), nullable=False)
	pwd=db.Column(db.String(50), nullable=False)

	def __repr__(self):
		return f"User(uname={self.uname}, pwd={self.pwd})"

class DishesModel(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	name=db.Column(db.String(50), nullable=False)
	cost=db.Column(db.Integer, nullable=False)
	image=db.Column(db.String(100), nullable=False)

	def __repr__(self):
		return f"Dish(name={self.name}, cost={self.cost}, image={self.image})"

#db.create_all() #used only once to create DB at start

user_args=reqparse.RequestParser()
user_args.add_argument("uname",type=str,help="Username can't be empty", location='headers', required=True)
user_args.add_argument("pwd",type=str,help="password can't be empty", location='headers', required=True)


dish_put_args=reqparse.RequestParser() #creating arguments with all required=True to use in updating all the fields.
dish_put_args.add_argument("name",type=str,help="Name can't be empty", required=True)
dish_put_args.add_argument("cost",type=int,help="Cost can't be empty", required=True)
dish_put_args.add_argument("image",type=werkzeug.datastructures.FileStorage, location='files',help="Image can't be empty", required=True)

dish_patch_args=reqparse.RequestParser() #creating arguments with all required=False(default) to use in updating particular fields.
dish_patch_args.add_argument("name",type=str,help="Name can't be empty")
dish_patch_args.add_argument("cost",type=int,help="Cost can't be empty")
dish_patch_args.add_argument("image",type=werkzeug.datastructures.FileStorage, location='files',help="Image can't be empty")

#format for serializing
resource_fields={
	'id':fields.Integer,
	'name':fields.String,
	'cost':fields.Integer,
	'image':fields.String
}

#for operations on particular dish
class Dish(Resource):
	def login(self):#for checking login credentials
		# username = request.headers.get("uname")#fetching uname from the FORM
		# userpass = request.headers.get("pass")#fetching pass from the FORM
		args=user_args.parse_args()
		user=users.query.filter_by(uname=args["uname"]).first()
		if(user.uname == args["uname"] and user.pwd== args["pwd"]): 
			return True
		abort(409, message = "Wrong username or password")

	@marshal_with(resource_fields) #for serializing in the resource_fields format
	def get(self,dish_id): #displaying dish info with id= dish_id
		if self.login():
			res = DishesModel.query.filter_by(id = dish_id).first() #selecting the record with id= dish_id
			if not res or (dish_id == 0):
				abort(404, message = "Dish Id doesn't exists..")
			return res

	@marshal_with(resource_fields)
	def put (self,dish_id): #for updating the entire dish info
		if self.login():
			args = dish_put_args.parse_args() #creating an instance of the parser
			result=DishesModel.query.filter_by(id=dish_id).first()
			if not result:
				abort(404, message="Dish Id doesn't exists, Can't update...")
			#updating all the fields
			result.name=args['name']
			result.image=str(args['image'])
			result.cost=args['cost']
			db.session.commit()
			return result, 201

	@marshal_with(resource_fields)
	def delete(self,dish_id):#for deleting dish with dish_id
		if self.login():
			dish = DishesModel.query.filter_by(id = dish_id).first()
			if not dish or (dish_id == 0):
				abort(404, message = "Dish Id doesn't exists..")
			db.session.delete(dish) 
			db.session.commit()
			return dish

	@marshal_with(resource_fields)
	def patch(self,dish_id): #for updating a dish partially
		if self.login():
			args=dish_patch_args.parse_args()
			result=DishesModel.query.filter_by(id=dish_id).first()
			if not result:
				abort(404, message="Dish Id doesn't exists, Can't update...")
			#updating only the requested field
			if args['name']:
				result.name=args['name']
			if args['image']:
				result.image=str(args['image'])
			if args['cost']:
				result.cost=args['cost']
			db.session.commit()
			return result,201

#for operations on all dishes in the DB
class Dishes(Resource):
	def login(self):#for checking login credentials
		args=user_args.parse_args()
		user=users.query.filter_by(uname=args["uname"]).first()
		if(user.uname == args["uname"] and user.pwd== args["pwd"]): 
			return True
		abort(409, message = "Wrong username or password")

	@marshal_with(resource_fields)
	def get(self): #displaying all the dishes
		if self.login():
			res=DishesModel.query.all()
			if not res:
				abort(404,message="No Dish Available...")
			return res

	@marshal_with(resource_fields)
	def post(self): #For adding new dishes
		if self.login():
			args=dish_put_args.parse_args()
			dish=DishesModel.query.all()
			if dish:
				for i in dish:
					if i.name==args["name"] and i.cost==args["cost"] and i.image==args["image"]:
						abort(409, message="Dish Already Available...")
			dish=DishesModel(name=args['name'],cost=args['cost'], image=str(args['image']))
			db.session.add(dish)
			db.session.commit()
			return dish, 201

	@marshal_with(resource_fields)
	def delete(self): #for deleting all dishes in the DB
		if self.login():
			dish=DishesModel.query.all()
			if not dish:
				abort(404,message="No Dish Available...")
			for i in dish:
				db.session.delete(i)
			db.session.commit()
			return dish

class signup(Resource): #signing up for new users
	def get(self): #displaying all users
		res=users.query.all()
		return res.__repr__()

	def post(self):
		args=user_args.parse_args()
		user=users.query.all()
		if user:
			for i in user:
				if i.uname==args["uname"] and i.pwd==args["pwd"]:
					abort(409, message="User Already exists...")
		user=users(uname=args['uname'], pwd=args['pwd'])
		db.session.add(user)
		db.session.commit()
		return {"message":"User Added"}, 201

api.add_resource(Dish,"/dishes/<int:dish_id>")
api.add_resource(Dishes, "/dishes")
api.add_resource(signup, "/signup")

if __name__=="__main__":
	# app.listen(process.env.PORT or 3000, 
	# function()
 #  		console.log("Express server listening on port %d in %s mode", this.address().port, app.settings.env);
	# );
	app.run(debug=True)
