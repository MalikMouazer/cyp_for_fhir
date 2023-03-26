import csv
import requests
# Web-scraping of:
# https://drug-interactions.medicine.iu.edu/MainTable.aspx
# Ouverture du fichier CSV en mode lecture
ddi_cyp = []
with open('cyp_ddi_scrap.csv', newline='') as csvfile:
    # Création d'un objet lecteur CSV
    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')

    # Parcours des lignes du fichier CSV
    for row in csv_reader:
        # Nettoyage des noms de médicaments
        cleaned_row = [name.strip().lower() for name in row]

        # Ajout de la ligne à la liste ddi_cyp
        ddi_cyp.append(tuple(cleaned_row))

# Liste de noms de médicaments en minuscules
ls_pa = ["citalopram", "amlodipine", "atorvastatin", "pantoprazole", "clopidogrel"]
print(len(ddi_cyp))

my_drugs = []
drugs = []
n = 0
for ddi in ddi_cyp:
    if(ddi[0] not in drugs):
        n += 1
        drugs.append(ddi[0])
        my_drugs.append((n, ddi[0]))

print("nb drugs  in db :", len(my_drugs))

substrates_ddi = []
not_sub_ddi = []
for ddi in ddi_cyp:
    if(ddi[2] == "substrates"):
        substrates_ddi.append(ddi)
    else:
        not_sub_ddi.append(ddi)

ddi_for_fhir = []
for victim in substrates_ddi:
    for perpet in not_sub_ddi:
        if(perpet[3] == "inhebitors"):
            effet = "Augmentation de la Bio disponibilité de %s"%(victim[0])
        else:
            effet = "Diminution de la Bio disponibilité de %s"%(victim[0])
        if(victim[1]==perpet[1]):

            ddi_for_fhir.append({"d1":victim[0],
                "d2":perpet[0],
                "type": "%s_%s_%s"%(perpet[3], perpet[1], perpet[2]),
                "incidence": effet,
            })



print("len sub :", len(substrates_ddi))
print("len non sub :", len(not_sub_ddi))

print("len FHIR DDI :", len(ddi_for_fhir))


print(ddi_for_fhir[2:6])



def get_cyp_fhir_ressource(inter):
    my_resource = """"{
  "resourceType" : "MedicinalProductInteraction",

  "subject" : [{ Reference(Medication/%s) }], 
  "description" : "Description clear", 
  "interactant" : [{
    "itemReference" : { Reference(Medication/%s) }
    "itemCodeableConcept" : { "text": "No more information" }
  }],
  "type" : { "text": "%s" }, 
  "effect" : { "text": "Interaction between two drugs" },
  "incidence" : { "text": "%s" }, 
  "management" : { "text" : "Adapatation posologique ou gestion du plan de prise sinon alternative therapeutique" } // Actions for managing the interaction
}"""%(inter["d1"], inter["d2"], inter["type"], inter["incidence"])

    return my_resource

print(get_cyp_fhir_ressource(ddi_for_fhir[89]))

host = 'https://fhir.st2c88fqxgfh.workload-nonprod-fhiraas.isccloud.io'
api_key = 'ton token'

def create_medication(my_drug):
    my_resource = """{
  "resourceType" : "Medication",
  "id" : "%s",
  "code" : {
    "coding" : [{
      "system" : "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code" : "%s",
      "display" : "%s"
    }]
  }
}"""%(my_drug[0], my_drug[1], my_drug[1])
    return my_resource, my_drug[0]

for drug in my_drugs:
    json_drug,id = create_medication(drug)
    # put the medication in the FHIR server
    url = host + '/Medication'
    # create the headers

    headers = {
        'Content-Type': 'application/json+fhir',
        'x-api-key': api_key
    }

    # make the request
    response = requests.put(url+'/'+str(id), headers=headers, data=json_drug)
    # raise an exception in case of http errors
    response.raise_for_status()
