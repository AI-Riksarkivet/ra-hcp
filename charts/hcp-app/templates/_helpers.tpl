{{/*
Expand the name of the chart.
*/}}
{{- define "hcp-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "hcp-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "hcp-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "hcp-app.labels" -}}
helm.sh/chart: {{ include "hcp-app.chart" . }}
{{ include "hcp-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "hcp-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hcp-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Redis fullname.
*/}}
{{- define "hcp-app.redisFullname" -}}
{{- printf "%s-redis" (include "hcp-app.fullname" .) }}
{{- end }}

{{/*
Redis selector labels.
*/}}
{{- define "hcp-app.redisSelectorLabels" -}}
app.kubernetes.io/name: {{ include "hcp-app.name" . }}-redis
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
