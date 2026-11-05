# UEBA and Behaviour-Based Insider Threat Detection: Academic Literature on Baselining and Risk Scoring

These are research notes (compiled 2026-11-04) on the academic and standards literature about User and Entity Behaviour Analytics (UEBA) and behaviour-based insider threat detection. They focus on how behaviour is baselined and turned into a risk score, so the report writer can compare it with the MCP gateway's behaviour multiplier (x0.7 to x5, self-baseline keyed by agent id, about 90 active days, a learned per-agent policy of tool limits and required steps, a bounded multiplier combined with a static risk floor). Commercial products and UEBA-for-AI-agents are out of scope; another researcher covers them. Verification method: every work was resolved against Crossref, OpenAlex, arXiv, DataCite, or the publisher or author PDF. I text-extracted 12 primary PDFs and read them for the specific claims quoted below; the other works are verified at metadata and abstract level. The second-pass count is at the end of the last section.

## 1. Definitions and origins: Gartner UBA (2014) to UEBA (2015), and the canonical UEBA pipeline

### Takeaway

Gartner named "User Behavior Analytics" in an August 2014 Market Guide and renamed it "User and Entity Behavior Analytics" in 2015 to cover non-human entities. The Gartner text itself is paywalled, so these notes use secondary quotes. The ideas are much older: per-subject statistical profiles of users, groups, remote hosts and the whole system, with aged baselines, come from Denning (1987) and SRI's IDES/NIDES (1988 to 1994). Fraud-detection profiling (1997 to 2008) supplied peer-group analysis. The canonical pipeline is: data sources, then per-entity features and profiles, then a self and/or peer baseline, then anomaly scoring, then aggregation into an entity risk score, then analyst triage under an alert budget with feedback.

### Cited Findings

- **Gartner 2014 (UBA).** Gartner published the "Market Guide for User Behavior Analytics" in August 2014. The authors were Avivah Litan and Mark Nicolett. In that guide UBA is about detecting insider threats, targeted attacks and financial fraud by finding meaningful anomalies in patterns of human behaviour. This is a secondary, vendor-hosted account — [Veriato blog, 2017](https://veriato.com/blog/the-rise-of-user-behavior-analytics/).
- A September 2014 press release quotes the 2014 guide: "User behavior analytics helps enterprises detect insider threats, targeted attacks, and financial fraud", and UBA "makes it much easier for enterprises to gain visibility into user behavior patterns in order to find offending actors and intruders". This is a vendor quote of Gartner, not the primary text — [Gurucul press release, 2014-09-09](https://gurucul.com/press-releases/gartner-recognizes-gurucul-as-a-key-vendor-in-2014-market-guide-for-user-behavior-analytics/).
- **Gartner 2015 (UEBA).** Gartner went from a 2014 UBA Market Guide to a 2015 UEBA Market Guide. Litan's stated reason, quoted: "The letter 'e' in the term UEBA recognizes the fact that other entities besides users are often profiled in order to more accurately pinpoint threats, in part by correlating the behavior of these other entities with user behavior." — [Dataconomy, 2016](https://dataconomy.com/2016/08/03/iot-security/). Vendor press releases date the 2015 guide to 22 September 2015, author Avivah Litan. I did not retrieve the primary text — [VentureBeat/ObserveIT, 2015](https://venturebeat.com/technology/observeit-recognized-in-2015-gartner-market-guide-for-user-and-entity-behavior-analytics).
- **Gartner 2016 definition (quoted by a Gartner analyst).** "User and entity behavior analytics offers profiling and anomaly detection based on a range of analytics approaches, usually using a combination of basic analytics methods (e.g., rules that leverage signatures, pattern matching and simple statistics) and advanced analytics (e.g., supervised and unsupervised machine learning). Vendors use packaged analytics to evaluate the activity of users and other entities (hosts, applications, network traffic and data repositories) to discover potential incidents". Chuvakin's gloss on the letters:
  - U: UEBA is user-centric.
  - E: it is not user-exclusive.
  - B: it focuses on behaviour, not roles or privileges.
  - A: it needs analytics beyond "hard-coded rules, thresholds and averages".

  Source: [Chuvakin, Gartner Blog Network, 2016-12-12 (archived)](https://chuvakin.blogspot.com/2016/12/ueba-clearly-defined-again.html).
- **Market trajectory.** Litan (Gartner) said the techniques fraud detection had used for decades (profiling, supervised and unsupervised learning) "have finally moved into security". She predicted UEBA would stop being a separate market and be absorbed into endpoint and IAM markets — [InfoRiskToday interview](https://www.inforisktoday.com/interviews/gartners-litan-on-endpoint-detection-behavioral-analytics-i-3456). The 2018 Gartner UEBA guide says that by 2021 UEBA "will cease to exist as a stand-alone category" as SIEM and UEBA converge — [Gartner 2018 Market Guide PDF (vendor-hosted)](https://intelligentcio.com/wp-content/uploads/sites/12/2019/01/gartner-market-guide-for-ueba-2018-analyst-report.pdf).
- **Academic origin (Denning).** Denning's intrusion-detection model (IEEE TSE, 1987) is the seminal statistical-profile model of subjects acting on objects, which is the root of UEBA baselining — [Denning 1987, doi:10.1109/TSE.1987.232894](https://doi.org/10.1109/TSE.1987.232894). An earlier version appeared at IEEE S&P 1986 — [doi:10.1109/SP.1986.10010](https://doi.org/10.1109/SP.1986.10010).
- **Academic origin (IDES/NIDES): entities and adaptive self-baselines.** The IDES statistical anomaly detector "adaptively learns what is normal for subjects. The defined subject types are individual users, groups, remote hosts and the overall system". It keeps only summary statistics per profile (frequency tables, means, covariances) and compares the whole vector of measures, "not just how the subject behaves with respect to each measure considered singly". These are users plus non-user entities, decades before Gartner's "E" — [Lunt et al., IDES final report, SRI, 1992](https://csl.sri.com/papers/9sri/9sri.pdf); [Javitz & Valdes, IEEE S&P 1991, doi:10.1109/RISP.1991.130799](https://doi.org/10.1109/RISP.1991.130799).
- **NIDES baselining principle.** "The basic statistical approach in NIDES is to compare a user's short-term behavior to the user's long-term behavior". This "requires no a priori knowledge about what types of behaviors would lead to compromised security" — [Javitz & Valdes, NIDES Statistical Component Description and Justification, SRI, 1994](https://csl.sri.com/papers/2sri/2sri.pdf).
- **Fraud-detection lineage.** Profiling of individual accounts — [Fawcett & Provost, "Adaptive Fraud Detection", DMKD 1997, doi:10.1023/A:1009700419189](https://doi.org/10.1023/A:1009700419189). Statistical fraud detection review — [Bolton & Hand, Statistical Science 2002, doi:10.1214/ss/1042727940](https://doi.org/10.1214/ss/1042727940). Peer group analysis — [Weston et al., "Plastic card fraud detection using peer group analysis", ADAC 2008, doi:10.1007/s11634-008-0021-8](https://doi.org/10.1007/s11634-008-0021-8).
- **Canonical pipeline in academic UEBA papers (Shashanka et al.).** UEBA modules "track and monitor behaviors of users, IP addresses and devices". They detect anomalies with SVD-based models and send alerts "to analysts with relevant contextual information" — [Shashanka, Shen & Wang, IEEE BigData 2016, doi:10.1109/BigData.2016.7840805](https://doi.org/10.1109/BigData.2016.7840805).
- **Canonical pipeline (Senator et al., DARPA ADAMS/PRODIGAL).** The team built "a visual language for specifying combinations of features, baselines, peer groups, time periods, and algorithms". The system ran on a real corporate database with independently built red-team inserts — [Senator et al., KDD 2013, doi:10.1145/2487575.2488213](https://doi.org/10.1145/2487575.2488213).
- **Canonical pipeline (AI^2).** The analyst-in-the-loop pipeline is: a behavioural analytics platform, then an outlier-detection ensemble, then analyst feedback, then a supervised module. On 3.6 billion log lines and 70.2 million entities it reports a 2.92x higher detection rate and more than 5x fewer false positives than unsupervised outlier analysis alone — [Veeramachaneni et al., IEEE BigDataSecurity 2016, doi:10.1109/BigDataSecurity-HPSC-IDS.2016.79](https://doi.org/10.1109/BigDataSecurity-HPSC-IDS.2016.79).
- **Academic UEBA definition (Landauer et al.).** "UEBA leverages anomaly detection techniques to recognize such intrusions by comparing user behavior patterns against profiles derived from historical log data" — [Landauer et al., IEEE BigData 2022, doi:10.1109/BigData55660.2022.10020672](https://doi.org/10.1109/BigData55660.2022.10020672).
- **Academic UEBA definition (Martín et al.).** UEBA relies "on statistical techniques and Machine Learning to determine when a significant deviation from patterns or trends established as a standard for users and entities is occurring" — [Martín et al., Computers & Security 2021, doi:10.1016/j.cose.2021.102356](https://doi.org/10.1016/j.cose.2021.102356).
- **UEBA effectiveness study.** A systematic review plus practitioner survey and interviews on UEBA against not-before-seen attacks — [Salitin & Zolait, 3ICT 2018, doi:10.1109/3ICT.2018.8855782](https://doi.org/10.1109/3ICT.2018.8855782).
- **Standards: NIST SP 800-207.** A "contextual" trust algorithm "takes the subject or network agent's recent history into consideration". The policy engine "must be informed of user behavior". "Analysis of subject behavior can be used to provide a model of acceptable use, and deviations from this behavior could trigger additional authentication checks or resource request denials" — [NIST SP 800-207 Zero Trust Architecture, 2020, §3.3.1, doi:10.6028/NIST.SP.800-207](https://doi.org/10.6028/NIST.SP.800-207).
- **Standards: NIST SP 800-53 Rev. 5, AC-2(12) "Account Monitoring for Atypical Usage".** The control requires organisations to "Monitor system accounts for [organization-defined atypical usage]" and report it. Atypical usage "includes accessing systems at certain times of the day or from locations that are not consistent with the normal usage patterns" — [NIST SP 800-53r5, 2020, doi:10.6028/NIST.SP.800-53r5](https://doi.org/10.6028/NIST.SP.800-53r5).

### Inferences

- The canonical UEBA pipeline maps one-to-one onto the gateway:
  - Data source: gateway log.
  - Entity: agent id.
  - Baseline: the learned per-agent policy plus 90-day history.
  - Anomaly scoring: the quiet and rising scenarios.
  - Entity risk: the bounded multiplier.
  - Triage: the gate, throttle or deny decision.

  The main structural difference is that the gateway multiplies a per-call static risk instead of producing a free-standing entity risk score that is queued for an analyst.
- NIST SP 800-207's "contextual, score-based" trust algorithm is the closest standards-level match to a behaviour multiplier on per-request risk. It also supports the threat-model framing that a policy engine should defend the resource using the subject's own history.
- "Entity" in UEBA has meant non-human subjects (hosts, IPs, applications, data stores) since 2015, and since IDES in the academic lineage. Treating an AI agent id as a UEBA entity is a direct extension, not a new concept.

### Gaps

- I could not retrieve the verbatim primary text of Gartner's 2014 UBA or 2015 UEBA Market Guides; they are paywalled. Definitions above come from vendor-hosted or analyst-blog quotes. In particular, the exact "five characteristics of UEBA vendors" list in the 2016 guide was not available.
- The IDES "enhanced prototype" SRI report (50-day half-life) did not show its year in the excerpt I retrieved. It is cited by URL only, in section 3.

## 2. Baselining methods: self-baselines, peer groups, seasonality, sequence models, graphs, isolation forest, autoencoders, clustering

### Takeaway

The literature uses all of these, and most systems combine them:
- **Self-baselines.** The oldest and still the default, usually with exponential aging (IDES/NIDES, Tuor).
- **Peer groups.** Used to separate an individual's change from an organisation-wide change, and to cope with sparse histories (Eldardiry, Legg, Turcotte).
- **Seasonality.** Time-of-day and weekday profiles.
- **Sequence models.** HMMs, LSTM/RNN language models, transformers.
- **Graph models.** Authentication and interaction graphs, GNNs, temporal link prediction.
- **Generic unsupervised detectors.** Isolation Forest, autoencoders, LOF, LODA, SVD/PCA.

No method dominates. Isolation Forest is repeatedly the strongest simple baseline, and the most recent work (2022 to 2026) is graph and transformer based.

### Cited Findings

**Self-baselines and profile aging**

- **IDES.** Profiles are updated daily. Before the update, counts, means and covariances are "aged by multiplying them by an exponential decay factor", which creates "a moving time window ... influenced most strongly by the most recently observed behavior". One IDES report uses a daily factor of 0.9862 (half-life 50 days) — [IDES: The Enhanced Prototype, SRI CSL report](https://www.csl.sri.com/papers/1sri/1sri.pdf). The 1992 final report recommends halving every 30 days — [Lunt et al., SRI 1992](https://csl.sri.com/papers/9sri/9sri.pdf).
- **NIDES short-term vs long-term.** The long-term profile half-life is 30 days. Short-term behaviour is a half-life in audit records, for example about 100 records for a short-term window of about 200 records. The NIDES authors note that waiting long enough to estimate full joint event probabilities is impractical: "we doubt that any system security officer would be willing to wait one or more years before starting anomaly detection on a new user" — [Javitz & Valdes, NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).
- **NIDES ages by activity, not the clock.** For non-intensity measures, age is counted in audit records rather than clock time. This "assures profile continuity over nights and weekends - periods when there is typically little activity". Only the three intensity measures use clock-time half-lives (1, 10 and 60 minutes) — [Javitz & Valdes, NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).
- **Tuor et al.: per-user baseline with a shared model.** One DNN or LSTM is "trained jointly over all users simultaneously and in an online fashion". It recognises "activity that is characteristic of each user", and the LSTM carries per-user hidden state across days. Features per user-day are counts of 408 activities, for example "uncommon non-decoy file copies from removable media between the hours of 12:00 p.m. and 6:00 p.m." This gives time-of-day bins. Six categorical attributes are added (role, project, functional unit, department, team, supervisor) — [Tuor et al., AAAI-17 Workshop on AI for Cyber Security, arXiv:1710.00811](https://arxiv.org/abs/1710.00811).
- **Le & Zincir-Heywood: recent-window representations.** Each data point is compared or concatenated with "a time window of the most recent data of the same user ... As concept shift and drift are likely in user behaviours, this may be more effective than normalizing all data instances of each user from the beginning". They use 7-day windows on LANL data — [Le & Zincir-Heywood, IEEE TNSM 2021, doi:10.1109/TNSM.2021.3071928](https://doi.org/10.1109/TNSM.2021.3071928); [author PDF](https://web.cs.dal.ca/~lcd/pubs/TNSM2021.pdf).

**Peer-group baselines**

- **Eldardiry et al.** They detect two kinds of anomaly:
  - "Blend-in anomalies", where malicious insiders try to behave like a group they do not belong to. These are found through inconsistencies across activity domains.
  - "Unusual change anomalies", where an insider's behaviour changes in a way "dissimilar to their peers' behavioral changes".

  The approach "avoids flagging common changes that can be mistakenly detected by typical temporal anomaly detection" — [Eldardiry et al., IEEE SPW (WRIT) 2013, doi:10.1109/SPW.2013.14](https://doi.org/10.1109/SPW.2013.14).
- **Legg et al.** Tree-structured profiles per user and per job role. Deviation is "the amount of variance that each user exhibits across multiple attributes, compared against their peers" — [Legg et al., IEEE Systems Journal 2017 (early access 2015), doi:10.1109/JSYST.2015.2438442](https://doi.org/10.1109/JSYST.2015.2438442).
- **Turcotte et al.: learned peer groups.** "Most existing approaches for modelling user behaviour rely on either independent observations for each user or on pre-defined user peer groups". They use Poisson factorisation (recommender-system style) to learn overlapping peer groups. It detected compromised accounts in a red-team exercise on authentication and process data from thousands of users — [Turcotte et al., IEEE ISI 2016, doi:10.1109/ISI.2016.7745472](https://doi.org/10.1109/ISI.2016.7745472). Related per-user modelling of LANL event logs — [Turcotte, Heard & Kent, in *Dynamic Networks and Cyber-Security*, 2016, doi:10.1142/9781786340757_0003](https://doi.org/10.1142/9781786340757_0003).
- **NIDES on group profiles.** Where "job classifications may be tightly prescribed ... it may be possible to develop useful group profiles, and individual profiles may not be necessary". NIDES nonetheless chose individual profiles for generality — [NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).
- **Per-user plus global baseline (Jordan & Chen, Enterprise GitHub).** 403M audit records, 147 days, 15K users. A combined per-user UEBA plus global outlier model flagged 26 anomalies. "A global-only baseline produced 64 alerts dominated by noisy service accounts" — [Jordan & Chen, IEEE SecDev 2025, doi:10.1109/SecDev66745.2025.00021](https://doi.org/10.1109/SecDev66745.2025.00021).

**Seasonality and time-of-day**

- **IDES weekday and weekend profiles.** IDES keeps separate profiles per "working status". "Weekend profiles are aged only on weekends, and weekday profiles are aged only on weekdays" — [IDES enhanced prototype report](https://www.csl.sri.com/papers/1sri/1sri.pdf).
- **Per-edge seasonality.** A per-edge seasonality plus nonparametric self-exciting (Wold-process) model of network connections beats standard seasonality and self-excitation models on Imperial College and LANL data — [Price-Williams & Heard, Statistics and Computing 2019/2020, doi:10.1007/s11222-019-09875-z](https://doi.org/10.1007/s11222-019-09875-z).
- **Temporal context matters but is hard to exploit on CERT.** Yuan & Wu note: "copying files in working hours looks normal, but copying files at mid-night is suspicious". In CERT data, however, "most of the activity time ... are randomly generated", so "there is no daily routine pattern" — [Yuan & Wu, Computers & Security 2021, doi:10.1016/j.cose.2021.102221](https://doi.org/10.1016/j.cose.2021.102221); [arXiv:2005.12433](https://arxiv.org/abs/2005.12433).

**Sequence models**

- **Masquerade detection on command sequences** (the classic Schonlau data) — [Schonlau et al., "Computer Intrusion: Detecting Masquerades", Statistical Science 2001, doi:10.1214/ss/998929476](https://doi.org/10.1214/ss/998929476); [Maxion & Townsend, DSN 2002, doi:10.1109/DSN.2002.1028903](https://doi.org/10.1109/DSN.2002.1028903).
- **HMMs.** Hidden Markov models learn each user's normal behaviour and flag significant deviations — [Rashid, Agrafiotis & Nurse, ACM MIST@CCS 2016, doi:10.1145/2995959.2995964](https://doi.org/10.1145/2995959.2995964).
- **LSTM over system-log keys** — [Du et al., DeepLog, ACM CCS 2017, doi:10.1145/3133956.3134015](https://doi.org/10.1145/3133956.3134015).
- **RNN language models over log lines** with a tiered user-level architecture. Log-line red-team detection AUC is 0.98 on LANL, beating Isolation Forest and PCA — [Tuor et al., arXiv:1712.00557 (2017)](https://arxiv.org/abs/1712.00557). An attention version adds interpretability — [Brown et al., arXiv:1803.04967 (2018)](https://arxiv.org/abs/1803.04967).
- **Other deep sequence work on CERT:**
  - [Yuan et al., ICCS 2018, doi:10.1007/978-3-319-93698-7_4](https://doi.org/10.1007/978-3-319-93698-7_4)
  - [Liu et al., IEEE Access 2019, doi:10.1109/ACCESS.2019.2957055](https://doi.org/10.1109/ACCESS.2019.2957055)
  - Transformers and self-attention: [DTITD, IEEE Access 2023, doi:10.1109/ACCESS.2023.3324371](https://doi.org/10.1109/ACCESS.2023.3324371); [hybrid TCN-transformer, Scientific Reports 2025, doi:10.1038/s41598-025-12063-x](https://doi.org/10.1038/s41598-025-12063-x)

**Graph-based models**

- **Authentication graphs**, analysing user behaviour within an enterprise network — [Kent, Liebrock & Neil, Computers & Security 2015, doi:10.1016/j.cose.2014.09.001](https://doi.org/10.1016/j.cose.2014.09.001).
- **Scan statistics** for locally anomalous subgraphs — [Neil et al., Technometrics 2013, doi:10.1080/00401706.2013.822830](https://doi.org/10.1080/00401706.2013.822830).
- **Login-structure model.** Normal logins modelled with market-basket patterns. 82% of malicious logins detected at 0.3% FPR on 5 months of real logins at a global financial company — [Siadati & Memon, ACM CCS 2017, doi:10.1145/3133956.3134003](https://doi.org/10.1145/3133956.3134003).
- **Unsupervised graph learning on LANL.** TPR 85% at FPR 0.9%, versus 72% and 4.4% for rule-based and non-graph baselines — [Bowman et al., RAID 2020](https://www.usenix.org/system/files/raid20-bowman.pdf).
- **Temporal GNN plus RNN link prediction** for lateral movement — [King & Huang, Euler, NDSS 2022, doi:10.14722/ndss.2022.24107](https://doi.org/10.14722/ndss.2022.24107); see also [Bian et al., IEEE TNSM 2021, doi:10.1109/TNSM.2021.3054356](https://doi.org/10.1109/TNSM.2021.3054356).
- **Insider-specific graph work:**
  - [Eberle, Graves & Holder, J. Applied Security Research 2010, doi:10.1080/19361610.2011.529413](https://doi.org/10.1080/19361610.2011.529413)
  - Graph learning plus psychological context: [Brdiczka et al., IEEE SPW 2012, doi:10.1109/SPW.2012.29](https://doi.org/10.1109/SPW.2012.29)
  - [Gamachchi et al., HICSS 2017, doi:10.24251/HICSS.2017.319](https://doi.org/10.24251/HICSS.2017.319)
  - Bipartite user-system graph after precipitating events such as layoffs: [Moriano et al., MIST 2017, doi:10.1145/3139923.3139928](https://doi.org/10.1145/3139923.3139928)
  - GCN: [Jiang et al., MILCOM 2019, doi:10.1109/MILCOM47813.2019.9020760](https://doi.org/10.1109/MILCOM47813.2019.9020760)
  - MEWRGNN: [Xiao et al., IEEE TNSM 2023, doi:10.1109/TNSM.2022.3222635](https://doi.org/10.1109/TNSM.2022.3222635)
  - Multi-timescale behaviour interaction graph, "abrupt and persistent threats": [SENTINEL, IEEE TNSE 2024, doi:10.1109/TNSE.2024.3519155](https://doi.org/10.1109/TNSE.2024.3519155)
  - Edge-level detection: [ADSAGE, Garchery & Granitzer, arXiv:2007.06985 (2020)](https://arxiv.org/abs/2007.06985)
  - Survey: [Gong et al., "Graph-based insider threat detection: A survey", Computer Networks 2024, doi:10.1016/j.comnet.2024.110757](https://doi.org/10.1016/j.comnet.2024.110757)

**Isolation Forest, autoencoders, other unsupervised detectors, clustering**

- **Isolation Forest.** Original method — [Liu, Ting & Zhou, ICDM 2008, doi:10.1109/ICDM.2008.17](https://doi.org/10.1109/ICDM.2008.17). Tuor et al. found Isolation Forest "the strongest" of their baselines (PCA, SVM, IF) — [arXiv:1710.00811](https://arxiv.org/abs/1710.00811). Gavai et al. used IF on real enterprise social and online activity with injected insider events (ROC 0.77). They aggregate which features contribute to isolating a point, to explain why a user was flagged — [Gavai et al., MIST 2015, doi:10.1145/2808783.2808784](https://doi.org/10.1145/2808783.2808784).
- **Autoencoder ensembles.** One autoencoder per audit-data category, scored by reconstruction error — [Liu et al., ICDMW 2018, doi:10.1109/ICDMW.2018.00014](https://doi.org/10.1109/ICDMW.2018.00014).
- **Le & Zincir-Heywood comparison.** They compare Autoencoder, Isolation Forest, LODA and LOF on CERT, LANL and TWOS data at day and week granularity — [IEEE TNSM 2021](https://web.cs.dal.ca/~lcd/pubs/TNSM2021.pdf). Related: [Le, Zincir-Heywood & Heywood, IEEE TNSM 2020, doi:10.1109/TNSM.2020.2967721](https://doi.org/10.1109/TNSM.2020.2967721); [Le & Zincir-Heywood, IEEE SPW 2018, doi:10.1109/SPW.2018.00043](https://doi.org/10.1109/SPW.2018.00043); [Int. J. Network Management 2020, doi:10.1002/nem.2109](https://doi.org/10.1002/nem.2109).
- **Other approaches.** SVD-based UEBA — [Shashanka et al. 2016](https://doi.org/10.1109/BigData.2016.7840805). Real-time streaming ensembles on heterogeneous data — [Böse et al., RADISH, IEEE Systems Journal 2017, doi:10.1109/JSYST.2016.2558507](https://doi.org/10.1109/JSYST.2016.2558507). User-behaviour modelling plus anomaly algorithms — [Kim et al., Applied Sciences 2019, doi:10.3390/app9194018](https://doi.org/10.3390/app9194018).
- **Clustering rejected in NIDES.** Cluster analysis was rejected because procedures "tend to be very sensitive to the identification of the proper seeds ... we do not believe that it would be appropriate for use in an anomaly detection system" — [NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).

### Inferences

- The gateway uses self-baselines only, keyed by agent id. This matches IDES/NIDES's default, but it departs from mainstream UEBA, which almost always adds peer or global baselines. Peer baselines serve two purposes:
  - They separate an individual's change from an organisation-wide change (Eldardiry). Without one, a legitimate org-wide rollout of a new MCP tool looks like a "rising" scenario for every agent.
  - They give sparse or new entities a prior (Turcotte, NIDES).

  Since there are no user ids, a peer group would have to be defined over agents: the same MCP server or route, the same tool set, or clusters learned from tool-usage vectors.
- The gateway's "90 active days" window is conceptually NIDES's choice to age by activity rather than wall-clock time, which preserves continuity over idle periods. The difference is a hard window rather than exponential aging. IDES/NIDES used half-lives of 30 to 50 days. NIDES explicitly argued that exponential weighting lets older behaviour count "smoothly and gradually" less, whereas a window counts everything inside it equally.
- The gateway's learned "limits per tool and required steps" policy is a hand-interpretable cross between per-feature count thresholds (Tuor-style count features) and a sequence model (HMM, DeepLog, required-step ordering). The literature's sequence models are probabilistic. The gateway's rules are crisp, which helps explainability but gives a coarser deviation signal.
- Jordan & Chen's finding, that global baselines are swamped by noisy service accounts, is direct evidence that machine identities need per-identity baselines. That supports the gateway's per-agent design.

### Gaps

- I found no academic study that quantitatively compares self-only, peer-only and combined baselines on the same data with machine (non-human) entities.
- I found no peer-reviewed paper that applies HMM, LSTM or transformer sequence baselines to MCP or tool-call sequences. The other researcher covers AI-agent-specific UEBA.

## 3. Risk scoring and aggregation: from per-event anomaly scores to an entity risk score

### Takeaway

Academic systems normalise heterogeneous anomaly scores, by percentile or rank, half-normal transform, or calibration to [0,1]. They then combine them. Options in use:
- Sum or mean of squares (NIDES T²)
- Sum of negative log-likelihoods (Tuor)
- Rank average, max or vote (Le 2021)
- p-value combiners (Fisher, Stouffer, Tippett)
- Bayesian networks
- "Repeated appearance near the top" over time (Goldberg 2016)
- Budget-constrained ranking (Ho 2017, Tuor CR-k)

Time decay is handled by exponentially weighted statistics (NIDES Q, Tuor EWMA). Bounding appears as normalisation to fixed ranges and as calibrated alert levels. I found no academic paper that formally analyses a bounded multiplicative behaviour modifier applied to a static risk score. The closest formal results are poisoning bounds under constraints (Kloft & Laskov) and the trust-algorithm taxonomy in NIST SP 800-207.

### Cited Findings

**NIDES: normalise each measure, then mean of squares, then calibrated alert levels**

- Each measure's statistic Q is mapped to S, "a simple mapping of the percentiles of the distribution of Q onto the percentiles of a half-normal distribution". The scores are then combined as "T² = (S₁² + S₂² + ... + Sₙ²)/n". The authors note T² "does not explicitly address the correlations among the Sᵢ". Cut-off values computed from historical T² define alert levels, each with "a corresponding false positive rate" — [Javitz & Valdes, NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).
- **Accumulation and alert hygiene.** Q "is the sum of audit record activity over the entire past usage, exponentially weighted so that the more current usage has a greater impact". Because "sequential values of T² are dependent, the T² values will slowly trend upward or downward". NIDES therefore notifies "only when a change occurs in the alert level" and clears the alert "whenever the T² value becomes sufficiently low" — [NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).

**Tuor et al.: likelihood scores with EWMA standardisation and per-feature decomposition**

- The anomaly score is a_t^u = −log P(x_t^u | h_{t−1}^u). Because the online model's scores "start out quite large ... and trend lower over time", they "compute an exponentially weighted moving average estimate of the mean and variance of these anomaly scores and standardize each score as it arrives".
- The score "decomposes as the sum over the negative log probabilities of our variables", down to per-feature terms (xᵢ − μᵢ)/σᵢ, which is what makes it explainable.
- Diagonal covariance beat identity covariance.
- Evaluation assumes a "daily budget" of user-days an analyst can review. The metric is Cumulative Recall CR-k = R(25)+R(50)+…+R(k). The best model put insider events at an average anomaly-score percentile of 95.53.

Source: [Tuor et al., arXiv:1710.00811](https://arxiv.org/abs/1710.00811).

**Le & Zincir-Heywood 2021: ensemble combination**

- Three schemes:
  - AVG: scores "normalized by rank, i.e. percentile transformation", then averaged.
  - MAX: the maximum of the rank-normalised scores, "the highest anomaly signal (alarm) generated ... by any of the participating models".
  - VOTE ν: majority vote at each investigation budget.
- Result: "AVG, VOTE 2,3, and AE ... significantly outperform the remaining algorithms (VOTE 4, MAX, IF, LODA, LOF)". MAX was among the weaker combiners.
- Headline numbers: "60% of malicious insiders are detected under 0.1% investigation budget, and all malicious insiders are detected at less than 5% investigation budget".

Source: [IEEE TNSM 2021, doi:10.1109/TNSM.2021.3071928](https://doi.org/10.1109/TNSM.2021.3071928); [author PDF](https://web.cs.dal.ca/~lcd/pubs/TNSM2021.pdf).

**Score normalisation and ensembles (general outlier detection)**

- Kriegel et al. show that outlier scores "differ widely in their meaning, range, and contrast". They propose translating arbitrary outlier factors "to values in the range [0, 1] interpretable as values describing the probability of a data object of being an outlier", which enables better ensembles — [Kriegel et al., SIAM SDM 2011, doi:10.1137/1.9781611972818.2](https://doi.org/10.1137/1.9781611972818.2).
- Theory of outlier ensembles (bias and variance, combination functions) — [Aggarwal & Sathe, SIGKDD Explorations 2015, doi:10.1145/2830544.2830549](https://doi.org/10.1145/2830544.2830549); open problems in combining unsupervised detectors — [Zimek, Campello & Sander, SIGKDD Explorations 2014, doi:10.1145/2594473.2594476](https://doi.org/10.1145/2594473.2594476).

**p-value combination (formal theory of how to aggregate anomaly evidence)**

- Heard & Rubin-Delanchy recast each p-value combiner as a likelihood-ratio test. Citing Birnbaum (1954), "any reasonable p-value combiner must be optimal against some alternative hypothesis". They then give theory for choosing a powerful combiner for the expected alternative. Only the abstract was checked — [Heard & Rubin-Delanchy, Biometrika 2018 (online 2017), doi:10.1093/biomet/asx076](https://doi.org/10.1093/biomet/asx076).

**Aggregation over time and alert budgets**

- **Goldberg et al.** "Providing a ranked or scored list of users ... is necessary but far from sufficient". High-risk users "may be identified by their repeated appearance near the top of the ranked and scored lists". Explaining and aggregating anomalies over time beat raw anomaly detection on the ADAMS/PRODIGAL data — [Goldberg, Young, Memory & Senator, HICSS 2016, doi:10.1109/HICSS.2016.344](https://doi.org/10.1109/HICSS.2016.344).
- **Multi-scale profiles.** Profiles at day, week and month scales and up a subject/object hierarchy. Current-vs-historical comparison gives an anomaly score, then related subjects are examined via subgraphs — [Kim et al., CSIIRW 2011, doi:10.1145/2179298.2179386](https://doi.org/10.1145/2179298.2179386).
- **Ho et al.: Directed Anomaly Scoring (DAS).** DAS ranks each event by "the total number of other events where E's feature vector is at least as suspicious as the other event in every feature dimension". It then raises the top N, where N is "the security team's alert budget". Deployment details: 10 alerts/day at LBNL, split across 3 sub-detectors, with a 6-month burn-in before alerting. On about 370M emails over about 4 years it ran under 10 alerts/day and found all but one known attack. Their motivation for not using per-feature anomaly: standard detectors "treat an event as anomalous even if only one or a few of the event's features are statistically anomalous" — [Ho et al., USENIX Security 2017](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf).
- **Alert correlation and triage beyond UEBA:**
  - [Valdes & Skinner, "Probabilistic Alert Correlation", RAID 2001, doi:10.1007/3-540-45474-8_4](https://doi.org/10.1007/3-540-45474-8_4)
  - Log-mining of enterprise logs — [Yen et al., Beehive, ACSAC 2013, doi:10.1145/2523649.2523670](https://doi.org/10.1145/2523649.2523670)
  - Provenance-based triage of alert fatigue — [Hassan et al., NoDoze, NDSS 2019, doi:10.14722/ndss.2019.23349](https://doi.org/10.14722/ndss.2019.23349)
  - [Hassan et al., RapSheet, IEEE S&P 2020, doi:10.1109/SP40000.2020.00096](https://doi.org/10.1109/SP40000.2020.00096)
  - HOLMES correlates suspicious information flows across APT stages into one "detection signal" — [Milajerdi et al., IEEE S&P 2019, doi:10.1109/SP.2019.00026](https://doi.org/10.1109/SP.2019.00026)

**Probabilistic and Bayesian entity risk**

- Bayesian network for insider motivation and psychology. When empirical psychological data were fed in, its predictions "approached the upper bound of model predictiveness" — [Axelrad et al., IEEE SPW 2013, doi:10.1109/SPW.2013.35](https://doi.org/10.1109/SPW.2013.35).
- Psychosocial risk model of "at-risk employees", validated against HR and management judgements — [Greitzer et al., HICSS 2012, doi:10.1109/HICSS.2012.309](https://doi.org/10.1109/HICSS.2012.309).

**Risk-adaptive access and trust algorithms (bounded, score-based decisions)**

- NIST SP 800-207 separates trust algorithms along two axes:
  - Criteria-based (all criteria must be met) vs score-based ("computes a confidence level based on values for every data source and enterprise-configured weights", compared with a per-resource threshold).
  - Singular vs contextual. A singular trust algorithm "does not take the subject history into consideration ... there is a risk that an attack can go undetected if it stays within a subject's allowed role".

  NIST concludes that "contextual, score-based TAs would provide the ability to offer more dynamic and granular access control" — [NIST SP 800-207, §3.3.1](https://doi.org/10.6028/NIST.SP.800-207).
- Fuzzy MLS makes access-control risk explicit and quantified, turning the Bell-LaPadula model into risk-adaptive control that behaves "more like a fuzzy logic control system" — [Cheng et al., IEEE S&P 2007, doi:10.1109/SP.2007.21](https://doi.org/10.1109/SP.2007.21).
- A recent example of a bounded entity score: a weekly employee risk score S ∈ [0,100], computed as a weighted sum of a rule-based layer, a statistical-deviation layer and an Isolation Forest layer (w = 0.30, 0.35, 0.35) — [Kartheek et al., MLBRS, DATA 2026, doi:10.5220/0015188200004091](https://doi.org/10.5220/0015188200004091).

**Formal bounds**

- For online centroid anomaly detectors with a sliding window, Kloft & Laskov derive bounds on poisoning. A poisoning attack "can be effectively staged in the unconstrained case", but "it can be made arbitrarily difficult (a strict upper bound on the attacker's gain) if external constraints are properly used", for example a bounded false-positive rate. They contrast this with infinite-memory learners, where attack effort grows exponentially but the learner cannot track legitimate drift — [Kloft & Laskov, JMLR 13, 2012](https://www.jmlr.org/papers/volume13/kloft12b/kloft12b.pdf).

**Trust and reputation analogues (decay, bounds, attacks)**

- The Beta reputation system combines positive and negative evidence into a bounded reputation score — [Jøsang & Ismail, Bled eConference 2002](https://aisel.aisnet.org/bled2002/41/).
- Survey of attacks and defences on reputation systems, classifying attacks by the design component they target — [Hoffman, Zage & Nita-Rotaru, ACM Computing Surveys 2009, doi:10.1145/1592451.1592452](https://doi.org/10.1145/1592451.1592452).

### Inferences

- The gateway multiplier (x0.7 to x5), applied to static per-call risk and floored, is a contextual score-based trust algorithm in NIST terms, layered on a criteria-based static floor. That layering is a defensible design: the floor guarantees a minimum regardless of history, which a pure singular or contextual scheme does not.
- Literature combiners suggest specific checks for the gateway's "max combiner" over dimensions:
  - Le 2021 found MAX among the weaker ensemble combiners on CERT. AVG and voting did better.
  - Heard & Rubin-Delanchy show every combiner is optimal only against some alternative. My reading, not checked in their full text: a max/min-p combiner suits evidence concentrated in one dimension, and Fisher- or mean-type combiners suit evidence spread across many.
  - Ho's DAS takes the opposite stance (anomalous in every dimension).

  An ablation of max vs mean vs Fisher-style combining is supported by the literature. It matches the existing ablation TODO.
- Bounding the multiplier is analogous to NIDES's half-normal or percentile mapping and Kriegel's [0,1] calibration: both stop one extreme dimension from dominating. Kloft & Laskov suggest bounds also limit what a poisoner can gain. The lower bound (0.7) is where a poisoner gains (a discount for "quiet" history). The upper bound (5) limits false-positive damage.
- NIDES's "notify only on alert-level change" and "clear when low" logic is a precedent for hysteresis in multiplier transitions. It prevents flapping between levels when the underlying statistic drifts slowly.
- A natural evaluation metric from this literature is the budget-based one (Tuor CR-k, Le's investigation budget, Ho's alerts/day). For a gateway, the analogue is "share of risky calls gated at a fixed share of benign calls throttled".

### Gaps

- I found no peer-reviewed paper that formally analyses a bounded multiplicative behaviour modifier on a static per-request risk score: monotonicity, a bound on attacker discount, or interaction with a floor. This appears to be an open gap the gateway design could claim, after a final check by the report writer.
- I did not retrieve HOLMES's exact severity-aggregation formula or Fuzzy MLS's exact risk function from full text. They are cited at abstract level only.
- The Beta reputation system's forgetting or aging mechanism was not re-checked in full text in this pass. Only the paper's existence and topic are verified.
- Literature on additive "risk accumulation with decay" per entity (the risk-based-alerting style) is almost entirely practitioner or commercial and out of scope. In academic venues I found only the NIDES exponentially weighted Q and Goldberg 2016's repeated-ranking aggregation.

## 4. Insider-threat detection literature: datasets (CERT r4.2/r6.2, LANL), benchmark results, key papers

### Takeaway

The CERT Insider Threat Test Dataset is the de facto benchmark. It is synthetic: r4.2 has 1,000 users and 70 insiders, and r6.2 has 4,000 users and 5 scenarios. Because evaluation protocols differ (granularity, budget, split), reported numbers are not comparable across papers. The LANL "Comprehensive, Multi-Source Cyber-Security Events" data is real: 58 days, 1.65 billion events, red-team labels, and it is the standard for authentication and lateral-movement graph work. All the key papers named in the brief exist and are verified. The "Liu et al. survey" in the brief is *Detecting and Preventing Cyber Insider Threats: A Survey* (IEEE COMST 2018); no "language modelling survey" by Liu was found. The RNN language-modelling papers are by Tuor et al. and Brown et al.

### Cited Findings

**CERT dataset**

- **Origin and caveats.** Glasser & Lindauer describe generating synthetic insider data for a DARPA research programme, "while discussing the benefits and limitations of synthetic insider threat data [and] the meaning of realism in this context" — [Glasser & Lindauer, IEEE SPW (WRIT) 2013, doi:10.1109/SPW.2013.37](https://doi.org/10.1109/SPW.2013.37). The dataset is archived as [Lindauer, "Insider Threat Test Dataset", CMU KiltHub 2020, doi:10.1184/R1/12841247](https://doi.org/10.1184/R1/12841247).
- **r4.2 and r6.2 counts (Yuan & Wu).** r4.2 has 1,000 employees, 70 insiders, 32,770,227 activities and 7,323 malicious activities. r6.2 has 5 insiders, 135,117,169 activities and 470 malicious activities. The same table lists 2,500 employees for r6.2 — [Yuan & Wu 2021, Table 2, arXiv:2005.12433](https://arxiv.org/abs/2005.12433). **This conflicts** with [Tuor et al. 2017](https://arxiv.org/abs/1710.00811): "Over the course of 516 days, 4,000 users generate 135,117,169 events ... five insider threat scenarios". The event counts agree, so the 2,500 figure is probably a table error.
- **Base rate on r6.2.** The anomaly rate is "in the order of 10⁻⁶ at event level or 10⁻⁵ at user-day level", and "there is no standard benchmark for the CERT problem" — [Garchery & Granitzer, ADSAGE, arXiv:2007.06985](https://arxiv.org/abs/2007.06985).

**LANL datasets**

- **Comprehensive, Multi-Source Cyber-Security Events.** 58 consecutive days; 1,648,275,307 events; 12,425 users; 17,684 computers; 62,974 processes. It contains auth, proc, flows, dns and redteam files, and red-team events are drawn from authentication data — [LANL data page](https://csr.lanl.gov/data/cyber1/); [Kent 2015, doi:10.17021/1179829](https://doi.org/10.17021/1179829); [Kent, in *Dynamic Networks and Cyber-Security*, 2016, doi:10.1142/9781786340757_0002](https://doi.org/10.1142/9781786340757_0002).
- **Unified Host and Network Data Set.** A follow-up LANL release, motivated by "the difficulty of balancing security and privacy concerns against the fidelity and utility of the data" — [Turcotte, Kent & Hash, arXiv:1708.07518 (2017)](https://arxiv.org/abs/1708.07518).
- **Real cloud UEBA dataset.** More than 5,000 users over more than five years from a cloud computing platform, with injected account-hijacking attacks. It exists because "simulations are unable to adequately induce the dynamic and unstable nature of real user behavior" — [Landauer et al., IEEE BigData 2022](https://doi.org/10.1109/BigData55660.2022.10020672).

**Key papers and headline results (as reported; not comparable across papers)**

- Tuor et al. 2017, CERT r6.2, online DNN/LSTM: insider events at an average 95.53 percentile; LSTM-Diag CR-400 = 11.6, CR-1000 = 35.6 — [arXiv:1710.00811](https://arxiv.org/abs/1710.00811).
- Tuor et al. 2017 on LANL (RNN language models): log-line AUC 0.98 — [arXiv:1712.00557](https://arxiv.org/abs/1712.00557).
- Le, Zincir-Heywood & Heywood 2020, supervised, multi-granularity, CERT: "up to 85% of malicious insiders are detected at only 0.78% false positive rate" — [doi:10.1109/TNSM.2020.2967721](https://doi.org/10.1109/TNSM.2020.2967721).
- Le & Zincir-Heywood 2021, unsupervised ensembles: 60% of insiders at a 0.1% budget, all at under 5% — [doi:10.1109/TNSM.2021.3071928](https://doi.org/10.1109/TNSM.2021.3071928).
- Gavai et al. 2015: ROC 0.77 on real data with injected insiders — [doi:10.1145/2808783.2808784](https://doi.org/10.1145/2808783.2808784).
- Bowman et al. 2020, LANL: TPR 85% at FPR 0.9% — [RAID 2020](https://www.usenix.org/system/files/raid20-bowman.pdf).
- Siadati & Memon 2017, real bank data: 82% at 0.3% FPR — [doi:10.1145/3133956.3134003](https://doi.org/10.1145/3133956.3134003).
- Other verified key papers:
  - [Rashid et al. 2016 (HMM)](https://doi.org/10.1145/2995959.2995964)
  - [Legg et al. 2017](https://doi.org/10.1109/JSYST.2015.2438442)
  - [Eldardiry et al. 2013](https://doi.org/10.1109/SPW.2013.14)
  - [Senator et al. 2013](https://doi.org/10.1145/2487575.2488213)
  - [Böse et al. 2017](https://doi.org/10.1109/JSYST.2016.2558507)
  - [Liu et al. 2018 autoencoders](https://doi.org/10.1109/ICDMW.2018.00014)
  - [Yuan et al. 2018](https://doi.org/10.1007/978-3-319-93698-7_4)
  - [Euler 2022](https://doi.org/10.14722/ndss.2022.24107)
- **Surveys named in the brief (verified):**
  - Yuan & Wu, "Deep learning for insider threat detection: Review, challenges and opportunities", Computers & Security 104 (2021) 102221 — [doi:10.1016/j.cose.2021.102221](https://doi.org/10.1016/j.cose.2021.102221).
  - Liu, De Vel, Han, Zhang & Xiang, "Detecting and Preventing Cyber Insider Threats: A Survey", IEEE COMST 2018. It organises work by traitor, masquerader and unintentional perpetrator, and by host, network or contextual data — [doi:10.1109/COMST.2018.2800740](https://doi.org/10.1109/COMST.2018.2800740).

### Inferences

- No standard CERT protocol exists, and the anomaly rate is extreme (10⁻⁵ per user-day). Published CERT numbers therefore support claims like "method X is competitive" but not absolute performance claims. The gateway's own evaluation should report budget-based recall at fixed throttle or deny rates, not only AUC.
- LANL is the closer analogue to gateway traffic: real, high-volume, machine-to-machine authentication events with sparse red-team labels. Its tool-call equivalent does not exist publicly. That is a further reason the project's own org-traffic corpora matter.

### Gaps

- I did not open the CERT dataset README, because the KiltHub page returned 403. The exact per-release user counts and scenario lists, and the r6.2 user-count conflict, therefore rest on the two papers above.
- No head-to-head re-benchmark of the main CERT methods under one protocol was found in this pass.

## 5. Known problems: false positives and base rates, drift, cold start, gradual poisoning, mimicry, privacy, explainability, synthetic evaluation

### Takeaway

The problems are well documented and old:
- **Base rates.** They make the false-alarm rate the limiting factor (Axelsson 2000).
- **False positives.** Most SOC "false positives" are benign true triggers (Alahmadi 2022).
- **Drift.** It is intrinsic to behaviour, so baselines must adapt.
- **Gradual poisoning.** Adaptation opens the door to "boiling frog" poisoning (Rubinstein 2009), with formal bounds only under external constraints (Kloft & Laskov 2012).
- **Mimicry.** Shown against sequence detectors since 2002, and blend-in insiders against peer models.
- **Privacy.** Monitoring creates privacy risk that NIST tells organisations to assess.
- **Explainability.** Required because accusations land on employees.
- **Synthetic data.** CERT's synthetic data limits how far results can be trusted.
- **Cold start.** Usually handled by burn-in periods, score standardisation or peer priors, not by dedicated research.

### Cited Findings

**False positives and base-rate fallacy**

- "The false alarm rate is the limiting factor for the performance of an intrusion detection system ... due to the base-rate fallacy". A substantial Bayesian detection rate P(Intrusion|Alarm) needs a "(perhaps in some cases unattainably) low false alarm rate" — [Axelsson, ACM TISSEC 2000, doi:10.1145/357830.357849](https://doi.org/10.1145/357830.357849).
- **Concrete illustration (Ho et al.).** Alerting on every email with a never-seen From name "would produce over 1.1 million alerts: a false positive rate of less than 1% on our dataset of nearly 370 million emails, but still orders of magnitude more than our target" — [Ho et al., USENIX Security 2017](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf).
- **SOC practitioners (Alahmadi et al.).** Practitioners confirmed high false-positive rates. "Most are attributed to benign triggers—true alarms, explained by legitimate behavior in the organization's environment". Alarm validation causes "alarm burnout and eventually desensitization". The authors propose five alarm properties: Reliable, Explainable, Analytical, Contextual, Transferable (REACT) — [Alahmadi, Axon & Martinovic, USENIX Security 2022](https://www.usenix.org/system/files/sec22-alahmadi.pdf).
- **Anomaly is not attack.** [Sommer & Paxson, IEEE S&P 2010, doi:10.1109/SP.2010.25](https://doi.org/10.1109/SP.2010.25); [Gates & Taylor, NSPW 2006, doi:10.1145/1278940.1278945](https://doi.org/10.1145/1278940.1278945); ten common ML-in-security pitfalls, including sampling bias and base-rate fallacy — [Arp et al., USENIX Security 2022, arXiv:2010.09470](https://arxiv.org/abs/2010.09470).

**Concept drift**

- Insider detection faces "hugely unbalanced data, limited ground truth, as well as behaviour drifts and shifts" — [Le et al., TNSM 2020](https://doi.org/10.1109/TNSM.2020.2967721).
- Insider behaviour "changes significantly after some types of precipitating events, such as layoffs, significant restructuring" — [Moriano et al., MIST 2017](https://doi.org/10.1145/3139923.3139928).
- Drift detection via conformal evaluation — [Jordaney et al., Transcend, USENIX Security 2017](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-jordaney.pdf); [Barbero et al., IEEE S&P 2022, doi:10.1109/SP46214.2022.9833659](https://doi.org/10.1109/SP46214.2022.9833659). Combined effect of drift and adversarial perturbation — [Apruzzese, Fass & Pierazzi, AISec 2024, doi:10.1145/3689932.3694757](https://doi.org/10.1145/3689932.3694757).

**Gradual poisoning ("boiling frog")**

- Attackers "could poison PCA slowly over long periods of time". The "Boiling Frog" scheme raises the false-negative rate as much as non-stealthy strategies "with far less chaff, albeit over a longer period of time". The defence is a robust-statistics PCA (ANTIDOTE), on which "poisoning has little effect" — [Rubinstein et al., ACM IMC 2009, doi:10.1145/1644893.1644895](https://doi.org/10.1145/1644893.1644895).
- Bounds on poisoning online centroid detectors: strict upper bounds on attacker gain only "if external constraints are properly used" — [Kloft & Laskov, JMLR 2012](https://www.jmlr.org/papers/volume13/kloft12b/kloft12b.pdf). Taxonomy of causative and exploratory attacks — [Barreno et al., ASIACCS 2006, doi:10.1145/1128817.1128824](https://doi.org/10.1145/1128817.1128824).
- **Insider-specific poisoning test (Le & Zincir-Heywood).** They trained with 0 up to all 70 CERT r4.2 insiders, so up to 35% of training users were malicious. "IF and LODA are very robust to the data poisoning attack". Performance "of AE and LOF deteriorates as the amount of malicious users in training increases", although AE stayed best up to 30 malicious users (15%) — [Le & Zincir-Heywood, TNSM 2021](https://web.cs.dal.ca/~lcd/pubs/TNSM2021.pdf).
- **Online-learning exposure (Tuor et al.).** The model is "trained ... in an online fashion" on the same stream it scores, which is the setting where gradual poisoning applies — [arXiv:1710.00811](https://arxiv.org/abs/1710.00811).

**Adversarial evasion and mimicry**

- Mimicry attacks against system-call sequence detectors — [Wagner & Soto, ACM CCS 2002, doi:10.1145/586110.586145](https://doi.org/10.1145/586110.586145); [Tan, Killourhy & Maxion, RAID 2002, doi:10.1007/3-540-36084-0_4](https://doi.org/10.1007/3-540-36084-0_4).
- Insiders who "behave similar to a group they do not belong to" (blend-in) — [Eldardiry et al. 2013](https://doi.org/10.1109/SPW.2013.14). Insiders "close in the feature space" to benign users, and "adaptive threats" — [Yuan & Wu 2021](https://arxiv.org/abs/2005.12433).
- Statistical mimicry of benign process profiles reduced provenance-detector detection rates "by up to 59%" — [Mukherjee et al., ProvNinja, USENIX Security 2023](https://www.usenix.org/system/files/usenixsecurity23-mukherjee.pdf).

**Cold start**

- NIDES: there is no willingness to wait "one or more years before starting anomaly detection on a new user". This is why it uses compact statistics and possible group profiles — [NIDES 1994](https://csl.sri.com/papers/2sri/2sri.pdf).
- Tuor's online model gives large scores at start-up, which are corrected by EWMA standardisation — [arXiv:1710.00811](https://arxiv.org/abs/1710.00811).
- Ho et al. used a six-month burn-in with no alerts — [USENIX Security 2017](https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-ho.pdf).
- Learned peer groups help users whose own history is sparse — [Turcotte et al. 2016](https://doi.org/10.1109/ISI.2016.7745472).

**Privacy and ethics**

- "Account monitoring may inadvertently create privacy risks since data collected to identify atypical usage may reveal previously unknown information about the behavior of individuals". Organisations must assess and document these risks — [NIST SP 800-53r5, AC-2(12)](https://doi.org/10.6028/NIST.SP.800-53r5).
- Over-surveillance "can violate legal requirements and data privacy principles" — [Gelman et al., arXiv:2608.21205 (2026)](https://arxiv.org/abs/2608.21205).
- Federated learning to avoid sharing insider data across organisations — [Wang et al., FedITD, IEEE Access 2024, doi:10.1109/ACCESS.2024.3482988](https://doi.org/10.1109/ACCESS.2024.3482988).
- Anonymisation "without loss of information" in a real UEBA dataset — [Landauer et al. 2022](https://doi.org/10.1109/BigData55660.2022.10020672).

**Explainability**

- "When an employee is detected as an insider, it is critical to understand the reason why ... false positive cases ... can seriously affect the loyalty of employees" — [Yuan & Wu 2021](https://arxiv.org/abs/2005.12433).
- Per-feature score decomposition — [Tuor 2017](https://arxiv.org/abs/1710.00811). Attention — [Brown 2018](https://arxiv.org/abs/1803.04967).
- User-day scoring leaves "which exact elements triggered it" open, which motivates event-level scoring — [ADSAGE 2020](https://arxiv.org/abs/2007.06985).
- XAI survey covering SHAP and LIME — [Saeed Alketbi et al., IEEE Access 2025, doi:10.1109/ACCESS.2025.3587114](https://doi.org/10.1109/ACCESS.2025.3587114).

**Evaluation on synthetic data**

- CERT activities are "randomly generated with limited complexity". The websites employees access are very limited, so "some insider threats, such as visiting wikileak.org, can be easily identified". There is "no daily routine pattern", and the insider scenarios are "narrow" — [Yuan & Wu 2021](https://arxiv.org/abs/2005.12433).
- Synthetic datasets "alleviate this problem to some extent" only — [Landauer et al. 2022](https://doi.org/10.1109/BigData55660.2022.10020672).
- LLM-generated synthetic insider data is a 2025 trend — [Ferraro et al., EAAI 2025, doi:10.1016/j.engappai.2025.111343](https://doi.org/10.1016/j.engappai.2025.111343); [Gelman et al., ISDFS 2025, doi:10.1109/ISDFS65363.2025.11012066](https://doi.org/10.1109/ISDFS65363.2025.11012066).

### Inferences

- The gateway's 0.7 lower bound is the exact surface for a boiling-frog attack. An agent that builds a long "quiet" history earns a 30% discount before a burst of risky calls. Two mitigations follow from the literature:
  - The static floor, which is a Kloft-style external constraint, already caps the discount.
  - Robust or trimmed statistics for the baseline (ANTIDOTE) and slow-to-forget anchors for high-risk tools would cap it further.

  It would be worth stating explicitly in the paper that history can never lower a call below its floor.
- "Rising" scenarios match the drift problem directly. Without peer or global context, an org-wide legitimate change in tool use looks like an individual rise, the false positive that Eldardiry's peer method was built to avoid.
- Because identity is only an agent id that may stand for the whole org, privacy risk is lower than in employee UEBA: there is no per-person monitoring. That is a positive difference worth stating, in line with AC-2(12)'s privacy note. The cost is that several humans' behaviour may be blended into one baseline, which widens it and helps mimicry.
- The literature's critique of CERT applies to the gateway's synthetic and simulated corpora. Pairing them with the real MCPHunt and gateway-captured traffic, as already planned, is consistent with Landauer's and Yuan & Wu's recommendations.

### Gaps

- I found no peer-reviewed work that measures boiling-frog poisoning specifically against per-entity UEBA baselines (user or agent) with time decay, as opposed to network-wide PCA or centroid models.
- I found no dedicated academic study of cold-start policies for UEBA entities (prior choice, burn-in length, peer fallback) with quantitative trade-offs.
- An apparent 2026 preprint on the "evasion-utility trade-off" on CERT surfaced only on a document-sharing site with anonymous authors. It is unverified and excluded.

## 6. Surveys 2015-2026, and UEBA ideas applied to APIs and machine or service identities

### Takeaway

Surveys run from Salem et al. (2008) through Homoliak et al. (2019, ACM CSUR) and Yuan & Wu (2021). Recent work moves to graph-based detection (2024), explainable AI (2025), and LLM-based detection (2024 to 2026). Academic work applying UEBA to APIs and machine identities is thin but growing:
- Per-identity baselining of cloud control-plane and SaaS audit logs (CloudTrail, GitHub Enterprise)
- Federated-identity session fingerprints
- NIST's contextual trust algorithms

Much of the "service account" material found is in low-quality venues. Only the items below were kept.

### Cited Findings

**Surveys, in chronological order**

- [Salem, Hershkop & Stolfo, "A Survey of Insider Attack Detection Research", in *Insider Attack and Cyber Security*, Springer 2008, doi:10.1007/978-0-387-77322-3_5](https://doi.org/10.1007/978-0-387-77322-3_5)
- General anomaly detection: [Chandola, Banerjee & Kumar, ACM CSUR 2009, doi:10.1145/1541880.1541882](https://doi.org/10.1145/1541880.1541882)
- Systematic review and meta-analysis: [Gheyas & Abdallah, Big Data Analytics 2016, doi:10.1186/s41044-016-0006-0](https://doi.org/10.1186/s41044-016-0006-0)
- [Liu et al., IEEE COMST 2018](https://doi.org/10.1109/COMST.2018.2800740)
- Structural taxonomy from the 5W1H questions and grounded-theory review: [Homoliak et al., "Insight Into Insiders and IT", ACM CSUR 2019, doi:10.1145/3303771](https://doi.org/10.1145/3303771)
- [Al-Mhiqani et al., Applied Sciences 2020, doi:10.3390/app10155208](https://doi.org/10.3390/app10155208)
- Ten challenges (imbalance, temporal information, fusion, subtle attacks, adaptive threats, fine-grained, early detection, explainability, lack of testbed, evaluation): [Yuan & Wu, Computers & Security 2021](https://doi.org/10.1016/j.cose.2021.102221)
- [Alzaabi & Mehmood, IEEE Access 2024, doi:10.1109/ACCESS.2024.3369906](https://doi.org/10.1109/ACCESS.2024.3369906)
- [Gong et al., graph-based ITD survey, Computer Networks 2024](https://doi.org/10.1016/j.comnet.2024.110757)
- Cyber-physical systems systematic review: [Computers & Electrical Engineering 2024, doi:10.1016/j.compeleceng.2024.109489](https://doi.org/10.1016/j.compeleceng.2024.109489)
- XAI for ITD: [Saeed Alketbi et al., IEEE Access 2025](https://doi.org/10.1109/ACCESS.2025.3587114)

**LLM-era insider-threat work (2024-2026)**

- Multi-agent LLM log auditing ("Decomposer" and "Tool Builder" agents, among others) — [Song et al., Audit-LLM, arXiv:2408.08902 (2024)](https://arxiv.org/abs/2408.08902)
- LLM-based log analysis for enterprise insider threats — [RedChronos, arXiv:2503.02702 (2025)](https://arxiv.org/abs/2503.02702), verified by metadata only.
- Federated LLM fine-tuning — [FedITD, IEEE Access 2024](https://doi.org/10.1109/ACCESS.2024.3482988)
- Cyber plus psychological data from 35 participants over 90 days — [GraphCH, IEEE TDSC 2024, doi:10.1109/TDSC.2024.3353929](https://doi.org/10.1109/TDSC.2024.3353929)

**UEBA for APIs and machine or service identities**

- UEBA over "users, IP addresses and devices" — [Shashanka et al. 2016](https://doi.org/10.1109/BigData.2016.7840805).
- **Federated identity.** A UEBA workflow lets relying parties in identity federations build a per-user "session fingerprint" from available information and raise alerts inside identity-management specifications. It is validated on an OpenID Connect web application — [Martín et al., Computers & Security 2021](https://doi.org/10.1016/j.cose.2021.102356).
- **Software supply-chain platform.** Per-user history-aware drift plus global Isolation Forest over GitHub Enterprise audit logs. Service accounts dominated global-only alerts — [Jordan & Chen, SecDev 2025](https://doi.org/10.1109/SecDev66745.2025.00021).
- **Cloud API (AWS CloudTrail).** A dynamic tripartite graph of users, services and actions, with a GNN scoring each user on historical activity. The data are 107,116 API calls over 32 days across 79 services, with 5 injected attacks. They report a 2 to 9% FPR reduction and 100% TPR, and note "there isn't a labeled dataset available to the public" — [Marbel et al., CS-GAD, arXiv:2409.12726 (2024)](https://arxiv.org/abs/2409.12726).
- **Cloud platform account hijacking.** A real 5-year, 5,000-user dataset with an adaptive detector — [Landauer et al. 2022](https://doi.org/10.1109/BigData55660.2022.10020672).
- **Standards hook.** NIST SP 800-207 applies contextual trust algorithms to "the subject or network agent", explicitly including non-human agents — [NIST SP 800-207](https://doi.org/10.6028/NIST.SP.800-207).

### Inferences

- The academic UEBA literature has barely studied machine and API identities. Where it has (GitHub audit logs, CloudTrail), per-identity baselines matter more than for humans, because global baselines are dominated by high-volume automation. An agent-id-keyed MCP gateway behaviour layer sits in this under-studied gap.
- No survey frames the protected asset as a tool server defended from its callers. The UEBA literature defends organisations from users. The MCP framing (server protected from agent) is a reorientation of UEBA from "who in my org is malicious" to "which caller is misusing this resource", the same shift NIST SP 800-207's per-resource policy engine makes.

### Gaps

- I found no peer-reviewed benchmark dataset for API-caller or service-identity behaviour with labelled misuse. CS-GAD and Landauer's dataset are the closest.
- A 2025 "Survey of Large Language Models for Insider Threat Detection" (doi:10.1109/CARS67163.2025.11337474) appeared in Semantic Scholar with an implausible venue label ("Computer Assisted Radiology and Surgery"). It is not used.

### Verification register (second pass)

Second pass completed 2026-11-04. I extracted every link from this file and de-duplicated them. Each cited work resolves to at least one authoritative record: Crossref, OpenAlex, arXiv API, DataCite, a publisher or author PDF, or the NIST, SRI or LANL site.

**Count of verified records cited: 113 unique records, which are 112 distinct works.** Denning's 1986 IEEE S&P and 1987 IEEE TSE versions count as one work.
- 93 DOI-registered records. These include 2 NIST standards (SP 800-207, SP 800-53r5) and 2 dataset DOIs (CERT/Lindauer 2020, LANL/Kent 2015).
- 10 arXiv-only works. The 11th arXiv ID, 2005.12433, is the preprint of Yuan & Wu's DOI-registered paper and is not counted twice.
- 10 works verified on publisher, author or institution sites without a DOI:
  - 5 USENIX/RAID PDFs: Ho 2017, Jordaney 2017, Bowman 2020, Alahmadi 2022, Mukherjee 2023
  - Kloft & Laskov, JMLR 2012
  - 3 SRI IDES/NIDES reports
  - Jøsang & Ismail 2002 (AIS eLibrary)

**Full-text checks.** For 12 works I extracted the PDF text and located each quoted claim: Tuor 2017, Yuan & Wu 2021, Le & Zincir-Heywood 2021, Rubinstein 2009, Kloft & Laskov 2012, Ho 2017, Alahmadi 2022, Bowman 2020, Jordaney 2017, NIDES 1994, NIST SP 800-207 and NIST SP 800-53r5. The two IDES reports were read through search-engine excerpts of the SRI PDFs. All other works were checked at metadata and abstract level (Crossref, OpenAlex or arXiv).

**Not counted as verified primary sources:** the Gartner Market Guides (2014, 2015, 2016, 2018), which were accessed only via vendor or analyst quotes, and the Dataconomy, Veriato, Gurucul, InfoRiskToday and VentureBeat pages used only to relay Gartner statements.

**Excluded as unverifiable or out of scope:**
- An anonymous 2026 "evasion-utility" preprint.
- Low-quality-venue "service account monitoring" papers.
- Patents.
- The mislabelled 2025 LLM-ITD survey.
- All commercial-product documentation.
