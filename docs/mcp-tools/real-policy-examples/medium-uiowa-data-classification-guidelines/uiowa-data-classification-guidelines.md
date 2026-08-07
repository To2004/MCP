# Data classification guidelines — The University of Iowa

> Verbatim text extraction of a **publicly published** policy page, kept as a
> real-world reference example. Copyright remains with the publisher.
>
> - Source: <https://itsecurity.uiowa.edu/it-policies/it-guidelines/data-classification-guidelines>
> - Retrieved: (cached)
> - Ladder rung: **medium** — Adds the CIA derivation matrix and five worked examples; one names a real system.

---

# Data classification guidelines

## Data classification guidelines

There are a few ways to help users/admins/data trustees readily determine the classification of a particular data set. If you are uncertain as to how to classify the data stored on or manipulated by your systems, refer to the following two examples – a process flow chart and below that matrix.

If the response is "Yes" to one or all of the following when changing or repurposing data, the chart below can assist with determining data sensitivity levels.

The matrix shows the three criteria that are used to define the data category for a given system or set of data. The criteria are Confidentiality, Integrity, and Availability, defined as follows:

Confidentiality refers to the privacy of an information asset. Specifically, confidentiality can be defined as which people, under what conditions, are authorized to access an information asset.

Integrity relates to the trustworthiness of data. There are two primary properties to consider when evaluating it. First, the notion that an asset should be trusted; there is an expectation that authorized users will only modify an asset in appropriate ways. The second aspect of integrity is when data is damaged, or incorrectly altered by authorized or unauthorized users, you must consider how important it is that the data be restored to a trustworthy state with minimum loss.

Availability describes the importance of information access by an authorized person, entity, service, or device when it’s needed, and the impact on the institution if it’s not available. As a general rule, the more time critical data is, the higher its availability ranking will be.

These criteria should be used to determine which data classification is appropriate. A positive response to the highest level in ANY row is sufficient to place the data into that respective classification. Use this chart to select the appropriate classification level for each of the following categories of confidentiality, integrity, and availability.

| | PUBLIC Low Sensitivity | UNIVERSITY-INTERNAL Moderate Sensitivity | RESTRICTED High Sensitivity | CRITICAL Very High Sensitivity | | | |
|---|---|---|---|---|---|---|---|
| Need for Confidentiality | Low Optional Public | Medium Recommended Non-Public or Internal | High Required Confidential | Very High Required Confidential | | | |
| | AND/ OR | AND/ OR | AND/ OR | AND/ OR | | | |
| Need for Integrity | Low Risk Optional Easily Reproducible | Medium Risk Recommended Internally Trusted | High Risk Required Official or Highly Trusted Data | Very High Risk Required Official or Highly Trusted Data | | | |
| | AND/ OR | AND/ OR | AND/ OR | AND/ OR | | | |
| Need for Availability | Low Impact Optional | Medium Impact Recommended Normal Services | High Impact Required Critical or Campus-wide service | Very High Impact Required Critical or Campus-wide or, externally required service | | | |

 

### Examples

This section illustrates how to classify some familiar data using the Confidentiality, Integrity, Availability (CIA) criteria.

Caveat: It should be noted that the ratings listed in the examples below are all based on the individual information asset. While it is important to identify and rate an asset on an individual basis, it is equally important to look at the other information assets that may be affected by a loss in confidentiality, integrity, or availability in the asset being rated.

### Online library catalog: university-internal data (moderate sensitivity)

InfoHawk+, the end-user interface to search the online library catalog has an optional (low) need for confidentiality since the catalog is public and we want students, faculty, staff and visitors to be able to find library resources. The need for integrity is recommended (medium risk) because we do not want records to be changed, whether by accident or maliciously.  The need for availability is recommended (medium impact) because there is no paper alternative and the University of Iowa probably wouldn’t experience a long-term loss of reputation and a long-term loss of research funding if the library catalog is unavailable for a short period of time.

### Summary data classification of online library catalog:

Need for Confidentiality is optional (low)

Need for Integrity is recommended (medium risk)

Need for Availability is recommended (medium impact)

Since at least one of the CIA conditions is recommended in this case both Integrity and Availability, the online library catalog is classified as University-Internal data and should be protected appropriately.

### Faculty Grade Books: university-internal data (moderate sensitivity)

The grade books faculty maintain with student id’s and grades has a recommended (medium) need for confidentiality since only the official records, transcripts are highly sensitive.  The need for integrity is recommended (medium risk) because we do not want the grades to be changed, whether by accident or maliciously.  The need for availability is recommended (medium impact) because there is no paper alternative and the University of Iowa probably wouldn’t experience a long-term loss of reputation and a long-term loss of research funding if an individual faculty members grade book is unavailable for a short period of time.

### Summary data classification of faculty student grades (grade books):

Need for Confidentiality is recommended (medium)

Need for Integrity is recommended (medium risk)

Need for Availability is recommended (medium impact)

Since at least one of the CIA conditions is recommended in this case Confidentiality, Integrity and Availability, faculty grade books are classified as University-Internal data and should be protected appropriately.

### Student Records: restricted data (high sensitivity)

Student records maintained by faculty with disciplinary issues or records containing social security numbers have a required need for confidentiality (high) since this information must never be publicly exposed due to federal laws like FERPA.  The need for integrity is recommended (medium risk) because we do not want these records to be changed, whether by accident or maliciously.  The need for availability is recommended (medium impact) because there is likely no paper alternative and the University of Iowa probably wouldn’t experience a long-term loss of reputation and a long-term loss of research funding if an individual faculty members student records were unavailable for a short period of time.

### Summary data classification of faculty student grades (grade books):

Need for Confidentiality is required (high)

Need for Integrity is recommended (medium risk)

Need for Availability is recommended (medium impact)

Since at least one of the CIA triad conditions is required, in this case Confidentiality, student records are classified as Restricted data and should be protected appropriately.

### Research Data: restricted data (high sensitivity)

Sensitive research data is required to be confidential (high) due to various factors, including human subject data (excluding PHI), intellectual property rights, large grant funding, etc.  Integrity of the research is required (high risk) because the data must be accurate and free from errors.  Availability is recommended (medium impact), because The University of Iowa is not necessarily in any danger or in violation of any law if the data is unavailable for a period of time.

### Summary of sensitive research data:

Need for Confidentiality is required (high)

Need for Integrity is required (high risk)

Need for Availability is recommended (medium impact)

Since at least one of the CIA triad conditions is required (high), in this case both Confidentiality and Integrity, research data is classified as Restricted data and should be protected appropriately.

### Professor's blog: public data (low sensitivity)

A blog is by its very nature designed to be shared with the world.  The confidentiality requirement is therefore optional (low).  If the contents of the blog are changed, there would be little to no impact on the ability of the department or the university to carry out their missions.  The need for integrity is therefore optional (low risk).  The need for availability is also optional (low impact) because, should the blog be taken offline for a period of time, the only primary people affected would be the readers of the blog.  The department and university should be able to carry on business as usual, while the blog was restored or recreated.

### Summary of a professor's blog hosted on a departmental server:

Need for Confidentiality is optional (low)

Need for Integrity is optional (low risk)

Need for Availability is optional (low impact)

Since at all of the CIA triad conditions are optional (low), a professor's blog hosted on a departmental server is classified as Public data and should be protected appropriately.

The confidentiality, integrity, and availability ratings are useful to help determine and assess the risk of your information assets. It helps create a better understanding of which assets are the most critical, as well as allowing you to prioritize and develop effective actions to protect the assets most at risk. Remember, some institutional data, particularly LEVEL III (High Sensitivity/ Restricted) data, must be protected according to specific criteria outlined in the University’s Institutional Data Access Policy.

### Patient care data: critical data (very high sensitivity)

Patient Care data is required to be confidential (very high) due to various factors, due to the impact on patients if data is breached, penalties imposed by HIPAA and other laws or regulations, and loss of reputation in case of breach.  Integrity of the data is required (very high risk) because erroneous data could lead to adverse treatment outcomes.  Availability is very high (very high impact), because care could be adversely impacted if access to data is delayed.

### Summary of patient care data:

Need for Confidentiality is required (very high)

Need for Integrity is required (very high risk)

Need for Availability is recommended (very high impact)

Since at least one of the CIA triad conditions is required (very high), in this case all three (Confidentiality, Integrity and Availability), patient care data is classified as Critical data and should be protected appropriately.

 

Updated 11/11/2022
