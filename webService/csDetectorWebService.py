import flask
import os, sys, time, stat
p = os.path.abspath('.')
sys.path.insert(1, p)
from flask import jsonify, request, send_file, url_for
from lib import csDetectorAdapter

app = flask.Flask(__name__, static_url_path="/static")
app.config['UPLOAD_FOLDER'] = "/"

@app.route('/getSmells', methods=['GET'])
def getSmells():
    needed_graphs = False
    date = None
    if 'repo' in request.args:
        repo = str(request.args['repo'])
    else:
        return "Error: No repo field provided. Please specify a repo.", 400

    if 'pat' in request.args:
        pat = str(request.args['pat'])
    else:
        return "Error: No pat field provided. Please specify a pat.", 400

    if 'user' in request.args:
        user = str(request.args['user'])
    else:
        user = "default" 

    if 'graphs' in request.args:
        needed_graphs = bool(request.args['graphs'])    
    if 'date' in request.args:
        date = request.args['date']
    try:
        os.mkdir("../out/output_"+user)
    except Exception as e:
        print('error creating folder', e)
        pass

    tool = csDetectorAdapter.CsDetectorAdapter()
    if date is not None:
        els = str(date).split("/")
        sd = els[2]+"-"+els[1]+"-"+els[0]
        formattedResult, result, config = tool.executeTool(repo, pat, startingDate=sd, outputFolder="out/output_"+user)
    else:
        formattedResult, result, config = tool.executeTool(repo, pat, outputFolder="out/output_"+user)

    paths=[]
    if needed_graphs:
        paths.append(os.path.join(config.resultsPath, f"commitCentrality_0.pdf"))
        paths.append(os.path.join(config.resultsPath, f"Issues_0.pdf"))
        paths.append(os.path.join(config.resultsPath, f"issuesAndPRsCentrality_0.pdf"))
        paths.append(os.path.join(config.resultsPath, f"PRs_0.pdf"))
    
    r = jsonify({"result": result, "files":paths})
    return r

@app.route('/uploads/<path:filename>')
def download_file(filename):
    fn = os.path.join(os.getcwd(), filename)
    return send_file(fn)
 
@app.route('/', methods=['GET'])
def home():
    user_language = request.accept_languages
    user_prefered = user_language[0][0]
    if (user_prefered == "pt-BR" or user_prefered == "pt"):
        return app.send_static_file('index.pt.html')
    return app.send_static_file('index.html')

@app.route('/getSmells/html', methods=['POST'])
def ping():
    print(request.form)
    repo = request.form.get('ghRepo')
    pat = request.form.get('ghToken')
    if not repo:
        return "Error: No repo field provided. Please specify a repo.", 400

    if not pat:
        return "Error: No pat field provided. Please specify a pat.", 400

    tool = csDetectorAdapter.CsDetectorAdapter()

    formattedResult, result, config = tool.executeTool(repo, pat, outputFolder="out/output_default")
    print("Detected Smells", formattedResult)

    return jsonify({"result": result})

app.run(port=5001, threaded=True)
