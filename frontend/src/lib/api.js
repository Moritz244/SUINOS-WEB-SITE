import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
});

export const fetchPropriedades = () => api.get("/propriedades").then((r) => r.data);
export const fetchPropriedade = (id) => api.get(`/propriedades/${id}`).then((r) => r.data);
export const createPropriedade = (payload) => api.post("/propriedades", payload).then((r) => r.data);
export const fetchAlertas = (params = {}) => api.get("/alertas", { params }).then((r) => r.data);
export const resolverAlerta = (id) => api.post(`/alertas/${id}/resolver`).then((r) => r.data);
export const fetchDejetos = (params = {}) => api.get("/dejetos", { params }).then((r) => r.data);
export const createDejeto = (payload) => api.post("/dejetos", payload).then((r) => r.data);
export const fetchDashFrivatti = () => api.get("/dashboard/frivatti").then((r) => r.data);
export const fetchDashPrefeitura = () => api.get("/dashboard/prefeitura").then((r) => r.data);
export const createLeitura = (formData) =>
  api.post("/leituras", formData, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
export const relatorioPdfUrl = () => `${API}/relatorio/viabilidade`;
