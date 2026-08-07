```
arm       server             n   exact  within1    MAE   bias  derived    org
nacombo   calendar_real     16     88%     100%   0.12  +0.00     3.12   3.12
nacombo   github_real       20     90%     100%   0.10  +0.00     3.15   3.15
nacombo   slack_real        20     80%     100%   0.20  +0.20     3.15   2.95
sensiso   calendar_real     16     88%     100%   0.12  +0.00     3.12   3.12
sensiso   github_real       20     90%     100%   0.10  +0.10     3.25   3.15
sensiso   slack_real        20     85%      95%   0.20  +0.20     3.15   2.95
sensnist  calendar_real     16     88%     100%   0.12  +0.00     3.12   3.12
sensnist  github_real       20     75%     100%   0.25  +0.25     3.40   3.15
sensnist  slack_real        20     55%      95%   0.50  +0.50     3.45   2.95
senscis   calendar_real     16     62%      88%   0.50  +0.38     3.50   3.12
senscis   github_real       20     80%     100%   0.20  +0.20     3.35   3.15
senscis   slack_real        20     60%      90%   0.55  +0.55     3.50   2.95

arm       scheme                         n   exact  within1    MAE   bias
nacombo   our register scheme (baseline)  56     86%     100%   0.14  +0.07
sensiso   ISO/IEC 27001 A.5.12          56     88%      98%   0.14  +0.11
sensnist  FIPS 199 / SP 800-60          56     71%      98%   0.30  +0.27
senscis   CIS-style coarse scheme       56     68%      93%   0.41  +0.38
```
