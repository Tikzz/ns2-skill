# ns2-skill

## Installation
Ensure you have Python >3.6 installed and it's the default one (run `python` and check the version)

```bash
pip install virtualenv
git clone https://github.com/Tikzz/ns2-skill.git
cd ns2-skill
virtualenv venv

# Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
python run.py
```

By default it listens for POST requests on port 8100. Configure the ExternalShuffle mod accordingly.


## Hive skill per teams method (Bleu)

### Teams:
    A = Aliens
    M = Marines

### Parameters:
    HS      = Player Hiveskill
    HS_X    = Player Hiveskill for team X (marines or aliens)
    WR(X,N) = Winrate of the last N games in team X
    N_X     = Quantity of matches played in team X
    P_X     = Weighting for player hiveskill in team X
    
#### Method to estimate per team hiveskill for team X (HS_X) with an history of N matches played in team X
    IF
        N_X => N
    THEN
        HS_X = HS * WR(X,N) * 2
    ELSE
        P_X = sqrt(N_X / N)
        HS_X = HS * [WR(X,N) *2 * P_X + (1 - P_X)]
    END IF

---

## Shuffle method

### 1. Generate all posible team combinations (not optimized for greater playercounts than 8v8)
### 2. For each combination, calculate:
  - Mean and standard deviation per team
  - Difference between team means and standard deviations
  - **`Score`**
  - **`RScore`**


#### Combination score (`Score`)
`Score = sqrt(diff_avg^2 + diff_std^2)`

While it may lack statistical basis, it's a decent way of sorting the resulting combinations that minimizes both `diff_avg` and `diff_std` equally.

#### Team repeat score (`RScore`)
Given the deterministic nature if the players available for shuffling stay the same, this is in place to reduce the likelihood of picking a shuffle combination that makes a lot of players end in a team side they played a lot recently.

`RScore = sum(proportion of last n matches played as marines, for each marine player) + sum(proportion of last n matches played as aliens, for each alien player)`

(*`n = 5` by default*)

### 3. Keep the combinations with `Score < score_cutoff`, discard the others.
(*`score_cutoff = 100` by default*)

### 4. From the remaining combinations, return the one with the least `RScore`.
