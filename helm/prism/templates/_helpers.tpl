{{/*
Expand the name of the chart.
*/}}
{{- define "prism.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "prism.fullname" -}}
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
{{- define "prism.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "prism.labels" -}}
helm.sh/chart: {{ include "prism.chart" . }}
{{ include "prism.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: prism
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "prism.selectorLabels" -}}
app.kubernetes.io/name: {{ include "prism.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "prism.api.labels" -}}
{{ include "prism.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "prism.api.selectorLabels" -}}
{{ include "prism.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Worker labels
*/}}
{{- define "prism.worker.labels" -}}
{{ include "prism.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "prism.worker.selectorLabels" -}}
{{ include "prism.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Scheduler labels
*/}}
{{- define "prism.scheduler.labels" -}}
{{ include "prism.labels" . }}
app.kubernetes.io/component: scheduler
{{- end }}

{{/*
Scheduler selector labels
*/}}
{{- define "prism.scheduler.selectorLabels" -}}
{{ include "prism.selectorLabels" . }}
app.kubernetes.io/component: scheduler
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "prism.serviceAccountName" -}}
{{- if .Values.api.serviceAccount.create }}
{{- default (include "prism.fullname" .) .Values.api.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.api.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "prism.image" -}}
{{- $registryName := .Values.global.imageRegistry | default .Values.image.registry -}}
{{- $repositoryName := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registryName }}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- else }}
{{- printf "%s:%s" $repositoryName $tag -}}
{{- end }}
{{- end }}

{{/*
Return the proper image pull secrets
*/}}
{{- define "prism.imagePullSecrets" -}}
{{- $pullSecrets := list }}
{{- if .Values.global.imagePullSecrets }}
  {{- range .Values.global.imagePullSecrets }}
    {{- $pullSecrets = append $pullSecrets . }}
  {{- end }}
{{- end }}
{{- if .Values.image.pullSecrets }}
  {{- range .Values.image.pullSecrets }}
    {{- $pullSecrets = append $pullSecrets . }}
  {{- end }}
{{- end }}
{{- if (not (empty $pullSecrets)) }}
imagePullSecrets:
  {{- range $pullSecrets | uniq }}
  - name: {{ . }}
  {{- end }}
{{- end }}
{{- end }}

{{/*
Return PostgreSQL hostname
*/}}
{{- define "prism.postgresql.hostname" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" (include "prism.fullname" .) -}}
{{- else }}
{{- .Values.externalPostgresql.hostname -}}
{{- end }}
{{- end }}

{{/*
Return Redis hostname
*/}}
{{- define "prism.redis.hostname" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis-master" (include "prism.fullname" .) -}}
{{- else }}
{{- .Values.externalRedis.hostname -}}
{{- end }}
{{- end }}

{{/*
Create a default database URL
*/}}
{{- define "prism.databaseUrl" -}}
{{- $hostname := include "prism.postgresql.hostname" . -}}
{{- $port := .Values.postgresql.service.port | default 5432 -}}
{{- $database := .Values.global.postgresql.auth.database -}}
{{- $username := .Values.postgresql.auth.username | default "postgres" -}}
{{- printf "postgresql://%s:$(POSTGRES_PASSWORD)@%s:%d/%s" $username $hostname $port $database -}}
{{- end }}

{{/*
Create a default Redis URL
*/}}
{{- define "prism.redisUrl" -}}
{{- $hostname := include "prism.redis.hostname" . -}}
{{- $port := .Values.redis.master.service.port | default 6379 -}}
{{- if .Values.redis.auth.enabled -}}
{{- printf "redis://:$(REDIS_PASSWORD)@%s:%d/0" $hostname $port -}}
{{- else -}}
{{- printf "redis://%s:%d/0" $hostname $port -}}
{{- end -}}
{{- end }}