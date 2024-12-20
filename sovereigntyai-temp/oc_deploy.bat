oc config use sovereignty-ai-dev/api-openshift-bmaas-int-tietoevry-com:6443/%username%
oc project sovereignty-ai-dev
oc apply -f persistent-volume/k8s
oc apply -f persistent-volume/k8s
oc apply -f services/database/k8s
oc apply -f services/llm/k8s
oc apply -f services/data-processor/k8s
oc apply -f services/embeddings/k8s
oc apply -f services/backend/k8s
oc apply -f services/frontend/k8s
