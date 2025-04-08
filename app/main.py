from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import logging
from mangum import Mangum
from .config import norm_path, de_norm_path, model_path
import pickle
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI(title="AI-CPAK API", version="0.1.0")
handler = Mangum(app)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

with open(norm_path, 'rb') as f:
	normalizer : MinMaxScaler = pickle.load(f)
	normalizer.feature_names_in_ = None # ["mpta", "ldfa"]
with open(de_norm_path, 'rb') as f:
	denormalizer : MinMaxScaler = pickle.load(f)
	denormalizer.feature_names_in_ = None # ["mpta", "ldfa"]
with open(model_path, 'rb') as f:
	model : MLPRegressor = pickle.load(f)
	model.feature_names_in_ = None # ["mpta", "ldfa"]

class PredictRequest(BaseModel):
	mpta: float
	ldfa: float

class PredictResponse(BaseModel):
	mpta: float
	ldfa: float

def predict(request: PredictRequest) -> PredictResponse:
	inpts = normalizer.transform(
		[[request.mpta, request.ldfa]]
	)
	preds = denormalizer.inverse_transform(model.predict(inpts))

	_mpta, _ldfa = preds[-1]

	return {"mpta": _mpta, "ldfa": _ldfa}


@app.get("/", response_class=HTMLResponse)
def pred_gui() -> str:
	return """
	<!DOCTYPE html>
	<html>
	<head>
		<title>AI CPAK Tool</title>
		<link rel="icon" href="/static/logo.png" type="image/x-icon">
		<style>
		body { font-family: Arial, sans-serif; margin: 20px; }
		label { display: inline-block; width: 100px; margin-bottom: 8px; }
		input { margin-bottom: 8px; }
		.result { margin-top: 12px; }
		</style>
	</head>
	<body>
		<h1>AI CPAK Tool</h1>
		<div>
		<label for="mpta">Pre-op MPTA</label>
		<input type="number" id="mpta" step="any" value="90">
		</div>
		<div>
		<label for="ldfa">Pre-op LDFA</label>
		<input type="number" id="ldfa" step="any" value="90">
		</div>
		<button onclick="predict()">Predict</button>

		<div class="result">
		<h3>Predicted MPTA: <span id="pred_mpta">None</span></h3>
		<h3>Predicted LDFA: <span id="pred_ldfa">None</span></h3>
		</div>
		<div class="images">
		<img src="static/MPTA_LDFA_knee.jpg" alt="MPTA vs LDFA diagram">
		<img src="static/aHKA.jpg" alt="aHKA diagram">
		<img src="static/JLO.jpg" alt="JLO diagram">
		</div>
		<div class="source_link">
		<a href="https://pubmed.ncbi.nlm.nih.gov/33517740/" > CPAK Paper </a>
		<br>
		<a href="https://github.com/JackBosco/AI_CPAK_webapp/" > Open Source </a>
		</div>


		<script>
		async function predict() {
			const pre_op_mpta = parseFloat(document.getElementById('mpta').value);
			const pre_op_ldfa = parseFloat(document.getElementById('ldfa').value);

			// POST to /predict with JSON body
			const response = await fetch("/api/predict", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ "mpta": pre_op_mpta, "ldfa": pre_op_ldfa })
			});
			const data = await response.json();

			// Update the displayed results
			document.getElementById("pred_mpta").textContent = data.mpta?.toFixed(2) ?? "None";
			document.getElementById("pred_ldfa").textContent = data.ldfa?.toFixed(2) ?? "None";
		}
		</script>
	</body>
	</html>
	"""


@app.post("/api/predict")
def pred_api(request: PredictRequest) -> PredictResponse:
	return predict(request)
