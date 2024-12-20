oc config use sovereignty-ai-dev/api-openshift-bmaas-int-tietoevry-com:6443/%username%
oc project sovereignty-ai-dev
oc start-build data-processor-build --from-dir=services
oc start-build embeddings-build --from-dir=services
oc start-build backend-build --from-dir=services
oc start-build frontend-build --from-dir=services
