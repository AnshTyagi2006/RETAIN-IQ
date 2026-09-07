# RetainIQ — Final End-to-End Testing Checklist

## 1. Authentication

- [ ] Home page opens without login
- [ ] Register with valid account
- [ ] Duplicate email is rejected
- [ ] Password shorter than 8 characters is rejected
- [ ] Login with correct credentials works
- [ ] Wrong password is rejected
- [ ] `/auth/me` returns the logged-in user
- [ ] Logout works
- [ ] Protected pages redirect after logout
- [ ] Protected APIs return 401 after logout

## 2. Manual Workflow

- [ ] Open Manual Analysis
- [ ] Submit valid customer
- [ ] Prediction appears
- [ ] Probability is displayed correctly
- [ ] Risk threshold works:
  - [ ] > = 0.70 = High Risk
  - [ ] > = 0.40 and < 0.70 = Medium Risk
  - [ ] < 0.40 = Low Risk
- [ ] Risk factors appear
- [ ] Protective factors appear
- [ ] SHAP explanation appears
- [ ] Retention action appears
- [ ] Manual result is saved to MySQL

## 3. Sample Workflow

- [ ] Sample page opens
- [ ] Sample analysis completes
- [ ] Global dashboard opens
- [ ] Total customer count is correct
- [ ] Risk counts are displayed
- [ ] Business segmentation is populated
- [ ] Retention Action Center is populated
- [ ] Customer Explorer works
- [ ] Sample data is NOT inserted into MySQL

## 4. Upload Workflow

- [ ] CSV upload works
- [ ] Excel upload works if supported
- [ ] Empty file is rejected
- [ ] Unsupported format is rejected
- [ ] Missing required columns are rejected
- [ ] Valid dataset is analyzed
- [ ] Global analytics appear
- [ ] Business segmentation appears
- [ ] Customer Explorer appears
- [ ] Customer drill-down works
- [ ] Upload dataset is saved to MySQL

## 5. Customer Explorer

- [ ] Search works
- [ ] Risk filter works
- [ ] Satisfaction filter works
- [ ] Complaint filter works
- [ ] Tenure filter works
- [ ] Category filter works
- [ ] Probability sorting works
- [ ] Clear Filters works
- [ ] Visible counts update correctly
- [ ] View Customer opens the correct customer

## 6. Customer 360 / SHAP

- [ ] Customer information is correct
- [ ] Probability matches bulk result
- [ ] Risk level matches bulk result
- [ ] Risk factors are shown
- [ ] Protective factors are shown
- [ ] SHAP values are readable
- [ ] Retention action is shown
- [ ] Recommendation is shown

## 7. Database Integrity

- [ ] Dataset record created
- [ ] Customer records linked to dataset
- [ ] Prediction records linked to dataset
- [ ] Explanations linked to dataset
- [ ] Re-running the same upload does not create unintended duplicate dataset records
- [ ] Customer/prediction/explanation counts are consistent
- [ ] Database failure does not crash the frontend

## 8. Edge Cases

- [ ] Missing JSON body
- [ ] Missing upload
- [ ] Empty upload
- [ ] Invalid dataset
- [ ] Missing dataset
- [ ] No current analysis
- [ ] No customers match filters
- [ ] Customer with missing optional values
- [ ] MySQL unavailable
- [ ] Model unavailable
- [ ] SHAP failure is handled cleanly

## 9. Performance

- [ ] Sample bulk prediction completes without bulk SHAP
- [ ] Global dashboard loads promptly
- [ ] Customer Explorer remains responsive
- [ ] SHAP is calculated only for individual customer analysis

## 10. Final Security Check

Current implementation includes authenticated sessions and per-user dataset ownership.

- [x] `user_id` added to datasets
- [x] Created datasets are associated with the logged-in user
- [x] Dataset retrieval is scoped by `user_id`
- [x] Customer retrieval is scoped through owned datasets
- [x] Dataset history is user-scoped
- [x] User A cannot access User B's dataset by changing an ID
- [x] Per-user file-hash reuse is enforced

## 11. Automated Tests

Run from the RetainIQ project root:

```bash
python -m pytest tests/test_retainiq_smoke.py -v
python -m pytest tests/security.py -v
```

Expected result: **30/30 tests passed**.



Run from the RetainIQ project root:

```bash
python -m pytest tests/test_retainiq_smoke.py -v
```

Fix any failure before deployment.

## Final Acceptance

RetainIQ is ready for deployment/documentation only when:

- authentication passes
- manual workflow passes
- sample workflow passes
- upload workflow passes
- customer explorer passes
- SHAP passes
- retention engine passes
- MySQL integrity passes
- edge cases pass
- ownership isolation passes
- smoke tests pass
