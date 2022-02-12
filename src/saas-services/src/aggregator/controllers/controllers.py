import flask
from flask.views import MethodView
from flask import request
import redis

app = flask.Flask(__name__)
app.config["DEBUG"] = True



# @app.route('/', methods=['GET'])
# def home():
#     return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"



class DataAggregator(MethodView):

    def get(self):
        return "200"


    def post(self):
        # print(self.post.__dir__())
        print(request.data)
        print(request.args)
        print(request.get_json())
        print(dir(request))
        return "201"

app.add_url_rule('/api/v1alpha1/gw/data-aggregator', view_func=DataAggregator.as_view('aggreagtor'))

app.run()