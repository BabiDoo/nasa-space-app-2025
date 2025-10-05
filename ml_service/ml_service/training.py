
import os
from pathlib import Path
from typing import Dict, Tuple, List, Literal, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report

Mission = Literal["kepler","k2","tess"]
Label = Literal["planet","non_planet","candidate"]

METRICS = {
    "accuracy": lambda y_true, y_pred: accuracy_score(y_true, y_pred),
    "f1_weighted": lambda y_true, y_pred: f1_score(y_true, y_pred, average="weighted", zero_division=0.0),
    "f1_macro": lambda y_true, y_pred: f1_score(y_true, y_pred, average="macro", zero_division=0.0),
    "precision_weighted": lambda y_true, y_pred: precision_score(y_true, y_pred, average="weighted", zero_division=0.0),
    "recall_weighted": lambda y_true, y_pred: recall_score(y_true, y_pred, average="weighted", zero_division=0.0),
}

def _map_labels(series: pd.Series) -> pd.Series:
    # Normalize labels found in the provided datasets
    mapping = {
        "not planet": "non_planet",
        "NOT PLANET": "non_planet",
        "non_planet": "non_planet",
        "planet": "planet",
        "candidate": "candidate",
        "CANDIDATE": "candidate",
        "CONFIRMED": "planet",
        "FALSE POSITIVE": "non_planet",
        "REFUTED": "non_planet",
    }
    return series.map(lambda v: mapping.get(str(v).strip(), "candidate"))

def load_dataset(mission: Mission) -> pd.DataFrame:
    here = Path(__file__).parent / "data" / mission / f"{mission}_data_treated.pkl"
    df = pd.read_pickle(here)
    df = df.copy()
    df["classification"] = _map_labels(df["classification"])
    # Keep only known classes
    df = df[df["classification"].isin(["planet","non_planet","candidate"])]
    return df

def _balance_df(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    # simple random undersampling to the size of the smallest class
    g = df.groupby("classification")
    n = g.size().min()
    parts = [grp.sample(n=n, random_state=seed, replace=False) for _, grp in g]
    return pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)

def _split(df: pd.DataFrame, seed: int = 42):
    X = df[["longitude","latitude","stellar_temperature","stellar_radius","planet_radius","eq_temperature","distance","stellar_sur_gravity"]]
    y = df["classification"]
    return train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)

def _models() -> Dict[str, Pipeline]:
    return {
        "gaussian_nb":   Pipeline([("clf", GaussianNB())]),
        "knn":           Pipeline([("scaler", StandardScaler()), ("clf", KNeighborsClassifier(n_neighbors=7))]),
        "decision_tree": Pipeline([("clf", DecisionTreeClassifier(max_depth=8, random_state=42))]), 
        "random_forest": Pipeline([("clf", RandomForestClassifier(n_estimators=200, random_state=42, class_weight=None))]),
        "log_reg":       Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=200, n_jobs=None, class_weight="balanced", multi_class="auto"))]),
    }

@dataclass
class ModelResult:
    mission: Mission
    model_name: str
    balanced: bool
    metrics: Dict[str, float]
    report: Dict[str, Any]

class ModelRegistry:
    def __init__(self):
        self.models: Dict[Tuple[Mission, str, bool], Pipeline] = {}
        self.results: Dict[Tuple[Mission, str, bool], ModelResult] = {}
        self.fitted: bool = False

    def fit_all(self, seeds: int = 42):
        for mission in ["kepler","k2","tess"]:
            df = load_dataset(mission)  # unbalanced
            df_bal = _balance_df(df)    # balanced

            for balanced, data in [(False, df), (True, df_bal)]:
                X_train, X_test, y_train, y_test = _split(data, seed=seeds)
                for name, pipe in _models().items():
                    model = pipe.fit(X_train, y_train)
                    key = (mission, name, balanced)
                    self.models[key] = model
                    y_pred = model.predict(X_test)
                    # compute metrics
                    mvals = {k: float(fn(y_test, y_pred)) for k, fn in METRICS.items()}
                    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0.0)
                    self.results[key] = ModelResult(mission=mission, model_name=name, balanced=balanced, metrics=mvals, report=report)
        self.fitted = True

    def predict(self, mission: Mission, features: Dict[str, float]) -> Dict[str, Any]:
        assert self.fitted, "Models not fitted."
        X = np.array([[
            features.get("longitude", 0.0),
            features.get("latitude", 0.0),
            features.get("stellar_temperature", 0.0),
            features.get("stellar_radius", 0.0),
            features.get("planet_radius", 0.0),
            features.get("eq_temperature", 0.0),
            features.get("distance", 0.0),
            features.get("stellar_sur_gravity", 0.0),
        ]])
        per_model = {}
        for model_name in ["gaussian_nb","knn","decision_tree","random_forest","log_reg"]:
            # prefer balanced models
            model = self.models[(mission, model_name, True)]
            proba = None
            if hasattr(model, "predict_proba"):
                try:
                    proba_arr = model.predict_proba(X)[0]
                    labels = list(model.classes_)
                    proba = {labels[i]: float(round(proba_arr[i], 6)) for i in range(len(labels))}
                except Exception:
                    proba = None
            label = str(model.predict(X)[0])
            per_model[model_name] = {
                "label": label,
                "proba": proba or {},
            }
        # ensemble: majority vote (planet vs non_planet; treat candidate as non_planet for the vote)
        votes = 0
        for m in per_model.values():
            l = m["label"]
            if l == "planet":
                votes += 1
            elif l == "non_planet":
                votes -= 1
            else:
                votes += 0  # candidate neutral
        label = "planet" if votes >= 1 else "non_planet"
        confidence = float(np.mean([max(v["proba"].get("planet", 0.0), v["proba"].get("non_planet", 0.0), v["proba"].get("candidate", 0.0)) or 0.0 for v in per_model.values()]))
        return {
            "per_model": per_model,
            "ensemble": {"rule": "majority_vote_candidate_neutral", "label": label, "confidence": confidence}
        }

    def list_datasets(self) -> Dict[str, Any]:
        out = {}
        for mission in ["kepler","k2","tess"]:
            df = load_dataset(mission)
            counts = df["classification"].value_counts().to_dict()
            out[mission] = {"rows": int(len(df)), "by_class": counts}
        return out

    def get_results(self, mission: Mission = None, model: str = None, balanced: bool = None) -> List[ModelResult]:
        items = list(self.results.values())
        def ok(mr: ModelResult) -> bool:
            return ((mission is None or mr.mission == mission) and
                    (model is None or mr.model_name == model) and
                    (balanced is None or mr.balanced == balanced))
        return [mr for mr in items if ok(mr)]

    def best_by(self, metric: str, balanced: bool = True) -> List[ModelResult]:
        sel = [mr for mr in self.results.values() if mr.balanced == balanced]
        by_mission: Dict[str, List[ModelResult]] = {"kepler": [], "k2": [], "tess": []}
        for mr in sel:
            by_mission[mr.mission].append(mr)
        out = []
        for mission, arr in by_mission.items():
            if not arr: 
                continue
            arr = sorted(arr, key=lambda x: x.metrics.get(metric, 0.0), reverse=True)
            out.append(arr[0])
        return out
