import type { PredictProps } from "../../types/predict.type";
import { formatDelay } from "../../utils/toolsDate";
import ButtonCustom from "../Button/ButtonCustom";

const ViewPredict = ({ dataPredict, onclick }: PredictProps) => {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            Prédiction de vol
          </h2>
          <p className="text-xs text-gray-400">{dataPredict.model_name}</p>
        </div>
        <span
          className={`text-xs font-medium px-3 py-1 rounded-full ${
            dataPredict.status === "NO DELAY"
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {dataPredict.status === "NO DELAY" ? "A l'heure" : "Retard"}
        </span>
      </div>

      {/* Retard estimé */}
      <div className="bg-gray-50 rounded-xl p-4 text-center mb-4">
        <p className="text-xs text-gray-400 mb-1">Retard estimé</p>
        {dataPredict.status === "NO DELAY" ? (
          <p className="text-3xl font-semibold text-green-600">A l'heure</p>
        ) : (
          <>
            <p className="text-3xl font-semibold text-red-600">
              {formatDelay(dataPredict.predicted_delay_minutes)}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {dataPredict.predicted_delay_minutes_raw.toFixed(2)} min (brut)
            </p>
          </>
        )}
      </div>

      {/* Route */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs text-gray-400">Départ</p>
          <p className="text-sm font-semibold">{dataPredict.origin.id_city}</p>
          <p className="text-xs text-gray-400">
            {dataPredict.origin.name_city}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Arrivée</p>
          <p className="text-sm font-semibold">
            {dataPredict.destination.id_city}
          </p>
          <p className="text-xs text-gray-400">
            {dataPredict.destination.name_city}
          </p>
        </div>
      </div>

      <hr className="border-gray-100 my-3" />

      {/* Infos vol */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs text-gray-400">Départ prévu</p>
          <p className="text-sm font-medium">
            {new Date(dataPredict.scheduled_departure).toLocaleString("fr-FR")}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Durée estimée</p>
          <p className="text-sm font-medium">
            {formatDelay(dataPredict.estimated_duration_minutes)}
          </p>
        </div>
      </div>
      <ButtonCustom size="md" variant="outline" onClick={onclick}>
        Nouvelle prédiction
      </ButtonCustom>
    </div>
  );
};

export default ViewPredict;
