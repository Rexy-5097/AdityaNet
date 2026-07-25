# Operator Casebook — V3 Solar Flare Alert Investigations

This document presents 20 case studies of alert investigations for model predictions on the test set. 

For each case, we report the query timestamp, prediction target, the top retrieved historical analogues from the training set, their similarity score, and their outcomes.

---

## Alert Investigation 0
- **Query Timestamp**: `2025-12-15T06:00:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 110686 | Timestamp: `2024-02-28T13:45:00` | Similarity: `0.9985` | Outcome: **Flare**
  2. Train Index 586596 | Timestamp: `2025-01-26T21:53:00` | Similarity: `0.9985` | Outcome: **Quiet**
  3. Train Index 621989 | Timestamp: `2025-02-20T19:51:00` | Similarity: `0.9985` | Outcome: **Quiet**

---

## Alert Investigation 1
- **Query Timestamp**: `2025-12-15T06:01:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9989` | Outcome: **Quiet**
  2. Train Index 531244 | Timestamp: `2024-12-19T07:46:00` | Similarity: `0.9988` | Outcome: **Flare**
  3. Train Index 571084 | Timestamp: `2025-01-16T02:32:00` | Similarity: `0.9988` | Outcome: **Quiet**

---

## Alert Investigation 2
- **Query Timestamp**: `2025-12-15T06:02:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 25388  | Timestamp: `2023-12-30T21:08:00` | Similarity: `0.9999` | Outcome: **Quiet**
  2. Train Index 529727 | Timestamp: `2024-12-18T06:29:00` | Similarity: `0.9999` | Outcome: **Quiet**
  3. Train Index 568789 | Timestamp: `2025-01-14T12:17:00` | Similarity: `0.9999` | Outcome: **Quiet**

---

## Alert Investigation 3
- **Query Timestamp**: `2025-12-15T06:03:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 133715 | Timestamp: `2024-03-15T13:39:00` | Similarity: `0.9999` | Outcome: **Quiet**
  2. Train Index 565568 | Timestamp: `2025-01-12T06:36:00` | Similarity: `0.9998` | Outcome: **Quiet**
  3. Train Index 499594 | Timestamp: `2024-11-27T04:17:00` | Similarity: `0.9998` | Outcome: **Quiet**

---

## Alert Investigation 4
- **Query Timestamp**: `2025-12-15T06:04:00`
- **Target Label**: `Flare` (High Alert)
- **Decision Alert Level**: Yellow/Red (Active alert warning)
- **Top 3 Historical Analogues**:
  1. Train Index 487605 | Timestamp: `2024-11-18T18:58:00` | Similarity: `0.9982` | Outcome: **Flare**
  2. Train Index 381474 | Timestamp: `2024-09-05T12:46:00` | Similarity: `0.9980` | Outcome: **Flare**
  3. Train Index 205406 | Timestamp: `2024-05-06T01:24:00` | Similarity: `0.9978` | Outcome: **Flare**

---

## Alert Investigation 5
- **Query Timestamp**: `2025-12-15T06:05:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 235693 | Timestamp: `2024-05-27T02:11:00` | Similarity: `0.9980` | Outcome: **Flare**
  2. Train Index 164318 | Timestamp: `2024-04-05T20:36:00` | Similarity: `0.9979` | Outcome: **Quiet**
  3. Train Index 400708 | Timestamp: `2024-09-18T22:17:00` | Similarity: `0.9979` | Outcome: **Quiet**

---

## Alert Investigation 6
- **Query Timestamp**: `2025-12-15T06:06:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 162656 | Timestamp: `2024-04-04T16:54:00` | Similarity: `0.9988` | Outcome: **Quiet**
  2. Train Index 38170  | Timestamp: `2024-01-08T18:51:00` | Similarity: `0.9988` | Outcome: **Quiet**
  3. Train Index 726078 | Timestamp: `2025-05-04T07:02:00` | Similarity: `0.9988` | Outcome: **Quiet**

---

## Alert Investigation 7
- **Query Timestamp**: `2025-12-15T06:07:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9991` | Outcome: **Quiet**
  2. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9989` | Outcome: **Quiet**
  3. Train Index 747319 | Timestamp: `2025-05-19T04:21:00` | Similarity: `0.9988` | Outcome: **Flare**

---

## Alert Investigation 8
- **Query Timestamp**: `2025-12-15T06:08:00`
- **Target Label**: `Flare` (High Alert)
- **Decision Alert Level**: Yellow/Red (Active alert warning)
- **Top 3 Historical Analogues**:
  1. Train Index 312606 | Timestamp: `2024-07-19T12:04:00` | Similarity: `0.9969` | Outcome: **Flare**
  2. Train Index 562144 | Timestamp: `2025-01-08T18:49:00` | Similarity: `0.9964` | Outcome: **Flare**
  3. Train Index 312607 | Timestamp: `2024-07-19T12:05:00` | Similarity: `0.9963` | Outcome: **Flare**

---

## Alert Investigation 9
- **Query Timestamp**: `2025-12-15T06:09:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 210961 | Timestamp: `2024-05-09T21:59:00` | Similarity: `0.9987` | Outcome: **Flare**
  2. Train Index 162656 | Timestamp: `2024-04-04T16:54:00` | Similarity: `0.9986` | Outcome: **Quiet**
  3. Train Index 726030 | Timestamp: `2025-05-04T06:14:00` | Similarity: `0.9985` | Outcome: **Quiet**

---

## Alert Investigation 10
- **Query Timestamp**: `2025-12-15T06:10:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 162656 | Timestamp: `2024-04-04T16:54:00` | Similarity: `0.9989` | Outcome: **Quiet**
  2. Train Index 726078 | Timestamp: `2025-05-04T07:02:00` | Similarity: `0.9988` | Outcome: **Quiet**
  3. Train Index 726030 | Timestamp: `2025-05-04T06:14:00` | Similarity: `0.9987` | Outcome: **Quiet**

---

## Alert Investigation 11
- **Query Timestamp**: `2025-12-15T06:11:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9991` | Outcome: **Quiet**
  2. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9989` | Outcome: **Quiet**
  3. Train Index 571084 | Timestamp: `2025-01-16T02:32:00` | Similarity: `0.9988` | Outcome: **Quiet**

---

## Alert Investigation 12
- **Query Timestamp**: `2025-12-15T06:12:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9995` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9994` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9992` | Outcome: **Quiet**

---

## Alert Investigation 13
- **Query Timestamp**: `2025-12-15T06:13:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9996` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9995` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9994` | Outcome: **Quiet**

---

## Alert Investigation 14
- **Query Timestamp**: `2025-12-15T06:14:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9996` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9995` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9994` | Outcome: **Quiet**

---

## Alert Investigation 15
- **Query Timestamp**: `2025-12-15T06:15:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9997` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9996` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9995` | Outcome: **Quiet**

---

## Alert Investigation 16
- **Query Timestamp**: `2025-12-15T06:16:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9998` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9997` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9996` | Outcome: **Quiet**

---

## Alert Investigation 17
- **Query Timestamp**: `2025-12-15T06:17:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9998` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9997` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9996` | Outcome: **Quiet**

---

## Alert Investigation 18
- **Query Timestamp**: `2025-12-15T06:18:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9998` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9997` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9996` | Outcome: **Quiet**

---

## Alert Investigation 19
- **Query Timestamp**: `2025-12-15T06:19:00`
- **Target Label**: `Quiet`
- **Decision Alert Level**: Green (No active warning)
- **Top 3 Historical Analogues**:
  1. Train Index 712979 | Timestamp: `2025-04-25T04:43:00` | Similarity: `0.9998` | Outcome: **Quiet**
  2. Train Index 727781 | Timestamp: `2025-05-05T11:25:00` | Similarity: `0.9997` | Outcome: **Quiet**
  3. Train Index 726244 | Timestamp: `2025-05-04T09:48:00` | Similarity: `0.9996` | Outcome: **Quiet**
