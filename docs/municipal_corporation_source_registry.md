# Municipal Corporation Source Registry Documentation
## Authoritative Web Endpoints, Resolution Trackers & GIS Map Repositories

### 1. Source Architecture
Each of the **29 Municipal Corporations** in Maharashtra is represented as an authoritative source record under `data/local_governments/sources/{corp_id}.json`.

These records track four vital categories of municipal information infrastructure:
1. **Public Web Portal:** The citizen-facing website hosting announcements, notices, and citizen charters.
2. **Citizen DBT / Welfare Portal:** The dedicated online application portal for social welfare, education grants, and urban health subsidies.
3. **Standing Committee Resolution Feeds:** The municipal gazette or resolution repository (` ठराव / इतिवृत्त`) documenting policy criteria and budget allocations.
4. **Spatial / GIS Ward Mapping:** The municipal GIS portal providing geo-spatial boundaries of administrative wards, ward offices, and electoral prabhags.

---

### 2. Representative Registry Entries

#### A. Brihanmumbai Municipal Corporation (`mc-brihanmumbai`)
- **Portal URL:** `https://portal.mcgm.gov.in`
- **DBT / Welfare URL:** `https://portal.mcgm.gov.in/irj/portal/anonymous/qlcitizenhome`
- **Resolution Source:** `https://portal.mcgm.gov.in/irj/portal/anonymous/qlresolution`
- **GIS Portal:** `https://mumbaigis.mcgm.gov.in`
- **Welfare Departments:** Planning Department, Social Welfare Cell, Education Officer.

#### B. Pune Municipal Corporation (`mc-pune`)
- **Portal URL:** `https://pmc.gov.in`
- **DBT / Welfare URL:** `https://dbt.pmc.gov.in`
- **Shahari Garib Arogya Portal:** `https://sgy.pmc.gov.in`
- **Resolution Source:** `https://pmc.gov.in/en/resolutions`
- **GIS Portal:** `https://punegis.pmc.gov.in`
- **Welfare Departments:** Urban Community Development (UCD), Social Development Department, Health Department.

#### C. Pimpri Chinchwad Municipal Corporation (`mc-pimpri-chinchwad`)
- **Portal URL:** `https://www.pcmcindia.gov.in`
- **DBT / Welfare URL:** `https://www.pcmcindia.gov.in/schemes.php`
- **Resolution Source:** `https://www.pcmcindia.gov.in/resolutions.php`
- **GIS Portal:** `https://smartpcmc.pcmcindia.gov.in/gis/`
- **Welfare Departments:** Social Welfare Department, Women and Child Welfare Committee, Divyang Welfare Cell.

#### D. Thane Municipal Corporation (`mc-thane`)
- **Portal URL:** `https://thanecity.gov.in`
- **DBT / Welfare URL:** `https://thanecity.gov.in/citizen-services`
- **Resolution Source:** `https://thanecity.gov.in/resolutions`
- **Welfare Departments:** Social Welfare Department, Education Board.

#### E. Navi Mumbai Municipal Corporation (`mc-navi-mumbai`)
- **Portal URL:** `https://www.nmmc.gov.in`
- **DBT / Welfare URL:** `https://www.nmmc.gov.in/navimumbai/social-welfare`
- **Welfare Departments:** Social Welfare Department, Sports & Cultural Department.

---

### 3. Registry Metadata Schema
```json
{
  "corporation_id": "mc-pimpri-chinchwad",
  "official_name_en": "Pimpri Chinchwad Municipal Corporation",
  "official_name_mr": "पिंपरी चिंचवड महानगरपालिका",
  "official_name_hi": "पिंपरी चिंचवड नगर निगम",
  "official_alternate_names": ["PCMC", "Pimpri Chinchwad Municipal Corporation"],
  "district": "Pune",
  "administrative_division": "Pune",
  "corporation_class": "A",
  "official_website": "https://www.pcmcindia.gov.in",
  "main_citizen_portal": "https://www.pcmcindia.gov.in/schemes.php",
  "ward_count": 8,
  "representative_wards": ["A Ward - Nigdi", "B Ward - Chinchwad", "C Ward - Bhosari", "D Ward - Pimple Saudagar"],
  "official_gis_portal": "https://smartpcmc.pcmcindia.gov.in/gis/",
  "welfare_departments": ["Social Welfare Department", "Women and Child Welfare Committee", "Divyang Cell"],
  "budget_source_url": "https://www.pcmcindia.gov.in/budget.php",
  "registry_status": "ACTIVE_VERIFIED"
}
```
