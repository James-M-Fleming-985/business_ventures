UK PATENT APPLICATION

SYSTEM AND METHOD FOR PREDICTIVE COMMUNICATION OUTCOME OPTIMISATION USING STRATEGIC VARIABLE MODELLING AND FEEDBACK CALIBRATION

ABSTRACT

A computer-implemented system enables users to predict and optimise interpersonal communication outcomes through multi-dimensional strategic variable modelling, probabilistic simulation, and closed-loop accuracy calibration. The system quantifies communication characteristics across five ontological layers, executes Monte Carlo simulations incorporating user-configurable confounding factors and strategy adjustments to generate probabilistic outcome predictions across three strategic dimensions (Notoriety, Respect, Financial Wealth), records empirical post-interaction observations, and calculates prediction accuracy metrics to refine future estimations. Novel technical contributions include a cognitive distortion logging system integrated with communication planning, a seven-dimensional strategic effectiveness measurement framework, a five-factor confounder penalty algorithm affecting skill performance, and a project management architecture specifically designed for communication objectives rather than generic deliverables. The system provides measurable technical advantages in sales optimisation, negotiation preparation, stakeholder management, and strategic relationship development by enabling systematic strategy testing and continuous prediction improvement through empirical validation.

TECHNICAL FIELD

This invention relates to computer-implemented systems for modelling, predicting, and optimising interpersonal communication outcomes. More specifically, it concerns methods and apparatus for quantifying communication variables across multiple ontological dimensions, generating probabilistic predictions of interaction outcomes through Monte Carlo simulation incorporating user-specific confounding factors and strategic adjustments, recording empirical post-interaction observations, calculating prediction accuracy metrics, and refining future predictions through closed-loop feedback mechanisms.

BACKGROUND ART

Effective interpersonal communication remains critical across professional domains including business development, negotiation, leadership, customer relations, and stakeholder management. Communication outcomes exhibit substantial variability and unpredictability due to complex interactions between cognitive capabilities, emotional states, sociocultural factors, behavioural patterns, and strategic objectives affecting both participants.

Existing technological approaches to communication improvement operate primarily in retrospective analysis mode. Conversation intelligence platforms such as Gong.io and Chorus.ai analyse recorded interactions to identify successful patterns and provide coaching recommendations, but function exclusively post-hoc without predictive capability before interactions occur. Customer relationship management systems including Salesforce and LinkedIn Sales Navigator track historical engagement metrics and relationship timelines, but lack sophisticated models of individual communication characteristics and cannot forecast specific interaction outcomes with quantified probability distributions before meetings take place.

Personality assessment tools including DiSC, Myers-Briggs Type Indicator, and platforms such as Crystal Knows provide static trait profiles based on questionnaire responses or limited behavioural observations. These systems generate broad characterisations but do not quantify situation-specific communication variables, model uncertainty through probability distributions, generate outcome predictions with confidence intervals, or adapt based on observed empirical results from actual interactions.

The fundamental limitations of prior art systems include the absence of comprehensive structured representation of communication variables spanning cognitive, emotional, sociocultural, behavioural, and strategic dimensions; probabilistic simulation engines generating outcome predictions before interactions occur; systematic recording and comparison of predicted versus actual outcomes; calculation of prediction accuracy metrics enabling quantifiable model improvement; and integration of cognitive awareness tools with communication planning workflows.

These limitations result in substantial inefficiency as communicators cannot systematically prepare for interactions with quantified outcome probabilities, test alternative strategies through simulation, identify optimal variable configurations for specific objectives, or benefit from cumulative learning across repeated interactions with empirical validation. There exists a need for a computer-implemented system that models communication variables with mathematical precision, generates probabilistic predictions through simulation accounting for real-time confounding factors, validates predictions against empirical outcomes, calculates measurable accuracy improvements, and provides integrated cognitive reflection capabilities linking psychological patterns to communication effectiveness.

SUMMARY OF INVENTION

The present invention addresses the aforementioned limitations through a computer-implemented system comprising a five-layer variable ontology for comprehensive communication representation; an actor profile data structure encoding individual characteristics; a simulation engine executing Monte Carlo iterations incorporating user-configurable confounding factors and strategic adjustments to predict interaction outcomes; a post-interaction recording module capturing empirical observations; an accuracy calculation engine comparing predictions to actuals; a cognitive distortion logging system integrated with communication planning; and a communication-specific project management framework.

The five-layer ontology quantifies cognitive variables (analytical reasoning, abstract thinking, pattern recognition, knowledge depth, learning rate, cognitive flexibility, memory capacity, processing speed), emotional variables (emotional intelligence, empathy, stress resilience, emotional stability, optimism bias, expressiveness, conflict tolerance), sociocultural variables (cultural fluency, social status sensitivity, authority response patterns, group identity strength, formality preference, network centrality), behavioural variables (communication style, verbosity, interruption tendency, question frequency, risk tolerance, decision speed, detail orientation), and strategic variables (goal clarity, strategic thinking, long-term orientation, negotiation skill, adaptability). Actor profiles store estimated values for these variables based on observable cues, with confidence scores tracking estimation uncertainty.

The system enables users (termed "Architects") to configure three core skills (Observation for accurately reading actor variables, Adaptation for flexibly adjusting strategies, Self-Awareness for recognising own biases and limitations) with values typically ranging from zero point three to zero point nine on a normalised zero-to-one scale. Five confounding variables modify effective skill levels in real-time: Stress Level reduces observation effectiveness by thirty percent and adaptation effectiveness by thirty percent; Fatigue Level reduces observation by twenty percent and adaptation by twenty percent; Emotional State reduces observation by twenty percent and self-awareness by thirty percent; Overconfidence reduces self-awareness by forty percent; Ego Investment reduces adaptation by thirty percent. These penalties compound multiplicatively such that an Architect with base observation skill of zero point eight experiencing stress level zero point six and fatigue level zero point four would have effective observation of approximately zero point five.

The simulation engine executes Monte Carlo iterations, typically one thousand runs but configurable from one hundred to ten thousand, sampling from actor variable distributions and applying confounder-adjusted skills to generate outcome predictions across three strategic dimensions: change in Notoriety, change in Respect, and change in Wealth. Five strategy levers (Warmth, Competence, Dominance, Status, Rapport) enable architects to configure intended communication approach on bipolar scales from negative one to positive one, with these adjustments incorporated into outcome calculation functions.

Novel technical contributions include a cognitive distortion logging system integrated with communication planning that records observed psychological elements, links episodes to specific actors who triggered them, creates Jungian polarity integration experiments as communication tasks, and feeds self-awareness metrics into skill calculations. A communication-specific project management architecture organises strategic interaction tasks rather than generic deliverables, with pre-configured templates for stakeholder alignment, conflict resolution, and relationship building scenarios. Post-interaction recording captures both predicted and actual values for confounders, strategy levers, and seven strategic effectiveness indexes, calculates prediction accuracy metrics, and identifies systematically misestimated variables for focused improvement.

DETAILED DESCRIPTION

System Architecture Overview

The invention is embodied in a computer system comprising processing hardware including central processing unit with floating-point arithmetic capabilities for Monte Carlo simulation, memory storage including random access memory for simulation execution and persistent database storage for actor profiles and historical interaction data, network communication interfaces providing application programming interface endpoints for data input and output, and user interface components comprising web-based visualisation dashboard accessible through standard internet browsers.

Figure 1 illustrates the overall system architecture comprising six primary modules operating in coordinated workflow. The Actor Profile Management Module stores and updates actor representations including estimated variable values, confidence scores, archetype classifications, and interaction history. The Simulation Engine Module executes Monte Carlo predictions incorporating architect state, confounder penalties, and strategy lever configurations. The Strategic Analytics Module calculates seven effectiveness indexes and generates optimization recommendations. The Post-Interaction Recording Module captures empirical observations after real-world interactions occur. The Cognitive Reflection Module logs psychological distortion episodes with linkage to triggering actors and creates integration tasks. The Communication Projects Module organises strategic interaction tasks with progress tracking and outcome measurement. Data flows left to right through the system: actor profile creation, pre-interaction simulation, strategy configuration, actual interaction occurrence, outcome recording, accuracy calculation, and model refinement for subsequent predictions.

The backend implementation utilises FastAPI framework providing representational state transfer application programming interface endpoints, PostgreSQL relational database version thirteen or higher for persistent storage with JSONB columns enabling flexible semi-structured data storage, NumPy and SciPy libraries for numerical computation, and SQLAlchemy object-relational mapping for database interactions. The frontend comprises a React single-page application implemented in TypeScript with real-time WebSocket connections for simulation progress updates and data visualisation using D3.js library for interactive charts and Recharts library for statistical graphics.

Strategic Outcomes Framework

The system optimises three user-configurable strategic outcomes measured across the architect's entire network of actor relationships. These outcomes provide quantitative targets for communication strategy rather than relying on subjective assessments of interaction quality.

Notoriety, denoted N, quantifies the degree to which relevant actors know, understand, and would support the architect's aims. The calculation aggregates three components for each actor in the network. Awareness measures whether the actor knows who the architect is and what they do, ranging from zero (no knowledge) through zero point five (knows name and role but limited context) to one (comprehensive knowledge of architect's work). Understanding measures whether the actor accurately comprehends the architect's strategic aims, ranging from zero (misconceptions or no understanding) through zero point five (partial understanding with gaps) to one (accurate comprehensive understanding). Support willingness measures whether the actor would actively help if asked, ranging from zero (would refuse or actively oppose) through zero point five (neutral or conditionally supportive) to one (would enthusiastically support).

The notoriety formula aggregates these components across all relevant actors:

N = (1/n) × Σ(i=1 to n) [awareness(i) × understanding(i) × support_willingness(i)]

where n represents the total number of relevant actors in the network. A notoriety value approaching zero indicates the architect is unknown or misunderstood in relevant networks, a value of approximately zero point five indicates moderate recognition with some support potential, and a value approaching one indicates widespread recognition, accurate understanding, and active support from key actors.

Change in notoriety from a single interaction, denoted ΔN, represents the incremental improvement or degradation resulting from that specific communication event. Interactions that successfully introduce the architect to new actors, correct misconceptions, or demonstrate value increase notoriety. Interactions that create negative impressions or fail to clarify aims decrease notoriety.

Respect, denoted R, quantifies the degree to which actors feel understood, valued, and believe their wants, needs, and desires are considered by the architect. This outcome measures relationship quality and mutual regard rather than mere awareness. The calculation aggregates three components analogous to notoriety. Feeling understood measures whether the actor feels the architect comprehends their perspective, ranging from zero (feels misunderstood, dismissed, or invisible) to one (feels deeply understood and validated). Consideration measures whether the actor believes their priorities are acknowledged, ranging from zero (priorities ignored or dismissed) to one (full recognition and consideration of actor's goals). Value alignment measures whether the actor perceives mutual benefit in engagement, ranging from zero (sees zero-sum relationship or exploitation) to one (sees strong win-win potential).

The respect formula follows identical structure:

R = (1/n) × Σ(i=1 to n) [feels_understood(i) × consideration(i) × value_alignment(i)]

Change in respect, ΔR, represents incremental improvement or degradation from specific interactions. Interactions demonstrating empathy, acknowledging actor concerns, and finding mutual benefits increase respect. Interactions appearing dismissive, self-serving, or tone-deaf decrease respect.

Financial Wealth, denoted W, quantifies economic value generation through salary increases, asset growth, cashflow improvements, opportunity pipeline development, and executed project value realisation. Unlike notoriety and respect which normalise to zero-one range, wealth is measured in absolute currency units, typically pounds sterling, and can span wide ranges from thousands to millions depending on the architect's career stage and objectives.

The wealth formula comprises three sub-components:

W = W_direct + W_pipeline + W_executed

Direct wealth, W_direct, includes salary increases (annual compensation growth in pounds or percentage change), asset growth (appreciating investments, property, equity stakes), and cashflow increases (net monthly or annual cash improvement). Pipeline wealth, W_pipeline, represents expected value of opportunities currently in progress, calculated as the sum across all opportunities of opportunity value multiplied by probability of execution. For example, an opportunity valued at fifty thousand pounds with seventy percent execution probability contributes thirty-five thousand pounds to pipeline wealth. Executed wealth, W_executed, represents realised gains from completed projects such as revenue increases, cost reductions, or investment returns.

The system enables architects to assign priority weights to each outcome based on current strategic focus, with weights denoted w_N, w_R, and w_W subject to the constraint that w_N + w_R + w_W equals one. An architect pursuing career advancement might configure weights of w_N equals zero point three, w_R equals zero point two, w_W equals zero point five, emphasising financial outcomes while maintaining moderate attention to visibility and relationships. An architect focused on relationship building might instead use w_N equals zero point two, w_R equals zero point six, w_W equals zero point two. These weights directly influence the ROI Index calculation described subsequently.

Seven Strategic Indexes

The system measures interaction effectiveness across seven strategic dimensions, providing multi-faceted assessment beyond simple outcome achievement. These indexes enable architects to diagnose interaction quality, identify improvement areas, and optimise process as well as results.

The ROI Index quantifies overall strategic value from an interaction, calculated as weighted sum of outcome changes scaled to zero-to-one-hundred range for interpretability. The formula is:

ROI_index = 50 + (50 × [w_N × ΔN + w_R × ΔR + w_W × ΔW_normalised])

where ΔN, ΔR represent changes in notoriety and respect (already normalised to approximately negative one to positive one range), ΔW_normalised represents change in wealth normalised by dividing by maximum possible wealth change for that interaction, and weights w_N, w_R, w_W reflect current strategic priorities. The baseline value of fifty represents neutral outcome with no change. Values above seventy-five indicate highly productive interactions with strong outcome advancement, values between fifty and seventy-five indicate moderately positive progress, values between forty and fifty indicate slightly positive outcomes with minimal gains, values between twenty-five and forty indicate slightly negative outcomes with setbacks, and values below twenty-five indicate highly negative interactions causing significant damage to strategic outcomes. The system tracks ROI Index across all interactions to identify high-value communication patterns and low-value activities requiring strategy adjustment.

Confidence Delta, denoted ΔC, quantifies change in the architect's confidence about actor variable estimates resulting from the interaction. Before interaction, the architect holds beliefs about actor variables with associated uncertainty. During interaction, observations may confirm existing estimates (high ΔC positive), reveal unexpected characteristics (high ΔC negative indicating previous misconceptions), or provide ambiguous signals (ΔC near zero). The calculation compares estimated variable values before interaction to updated estimates after incorporating observed behaviours. High positive confidence delta indicates the interaction successfully reduced uncertainty through clear behavioural signals. Negative confidence delta indicates the interaction introduced confusion or revealed previous estimates were inaccurate. This metric enables the system to track the architect's improving observation skills over time, as more experienced architects achieve consistently positive confidence delta through accurate initial estimates subsequently confirmed.

Resistance Index, denoted I_resistance, quantifies degree of friction, pushback, or misalignment encountered during interaction on zero-to-one scale. The calculation aggregates observed resistance signals including verbal objections (phrases such as "I don't think that will work" or "We tried that before"), non-verbal cues (crossed arms, leaning back, frowning), avoidance behaviours (deflection, topic changing, meeting postponement), delayed responses (slow replies, missed deadlines), and passive aggression (compliance without commitment). Each resistance signal is assigned an intensity value from zero point two (mild skepticism easily addressed) through zero point five (moderate pushback requiring negotiation) to one point zero (dealbreaker with complete refusal). The resistance index sums frequency multiplied by intensity for all observed signals, normalised to zero-one range. Values approaching zero indicate smooth aligned interaction with high receptivity, values around zero point five indicate moderate friction requiring skilled navigation, and values approaching one indicate high opposition or fundamental misalignment. The system uses resistance index to recommend alternative strategies for high-resistance actors and identify scenarios requiring additional preparation or different approaches.

Energy Cost, denoted E_cost, quantifies cognitive and emotional load required for the interaction on zero-to-one scale. The calculation combines cognitive load (mental effort from information density, decision difficulty, novel concepts, and concurrent concerns) and emotional load (effort to manage own emotional state, navigate interpersonal tension, and maintain composure under pressure). The formula is:

E_cost = (cognitive_load + emotional_load) / 2

where cognitive_load incorporates complexity (information density and decision difficulty), unfamiliarity (inverse of actor familiarity requiring more mental effort), and multitasking (number of concurrent objectives or concerns), and emotional_load incorporates stress (perceived stakes and anxiety), regulation effort (energy expended managing emotional reactions), and tension (interpersonal friction or discomfort). Additionally, confounding factors modify energy cost such that low energy levels, high fatigue, high stress, and physical exhaustion increase perceived energy cost for equivalent interactions. Values approaching zero indicate effortless energising interactions that leave the architect feeling refreshed, values around zero point five indicate moderate effort consistent with professional norms, and values approaching one indicate exhausting draining interactions causing significant fatigue. The system tracks energy cost relative to ROI Index to identify inefficient interactions (high energy cost, low ROI) requiring strategy adjustment and efficient interactions (low energy cost, high ROI) worth replicating.

Influence Depth, denoted I_depth, quantifies degree of internal belief or behaviour change achieved in the actor on zero-to-one scale. Superficial influence might change an actor's stated position without changing underlying beliefs (low influence depth), whereas deep influence shifts fundamental perspectives or behavioural patterns (high influence depth). The system distinguishes compliance (actor agrees but without conviction), identification (actor accepts architect's position because they respect the source), and internalisation (actor genuinely adopts new beliefs as their own). Values approaching zero indicate no lasting impact beyond polite acknowledgment, values around zero point five indicate moderate influence such as stated agreement or tentative behaviour change, and values approaching one indicate profound shifts in actor's worldview or sustained behaviour modification. This metric enables architects to assess whether interactions achieve surface-level compliance or genuine transformation.

Narrative Coherence, denoted I_narrative, quantifies consistency and clarity of the architect's message across the interaction on zero-to-one scale. High narrative coherence indicates the architect maintained a clear compelling story connecting all discussion points to overarching themes. Low narrative coherence indicates scattered messaging, contradictions, or unclear connections between topics. The calculation assesses message clarity (how easily the actor could summarise the architect's key points), internal consistency (absence of contradictions or confusing shifts), thematic unity (how well individual points connected to central narrative), and memorable structure (whether the interaction followed a coherent beginning-middle-end progression). Values approaching zero indicate confusing disjointed communication leaving the actor uncertain about main messages, values around zero point five indicate functional communication with room for improved clarity, and values approaching one indicate exceptionally clear memorable messaging that the actor could easily explain to others. This metric helps architects identify whether poor interaction outcomes stem from strategic content issues or presentation and delivery problems.

Confounder Penalty System

The system incorporates five confounding variables that degrade architect skill effectiveness during interactions, providing realistic simulation accounting for human performance limitations under sub-optimal conditions. These confounders operate through multiplicative penalty factors applied to base skill levels.

Stress Level, ranging from zero (completely relaxed) to one (maximum stress), reduces observation skill effectiveness by thirty percent and adaptation skill effectiveness by thirty percent. The effective observation skill becomes base_observation multiplied by quantity one minus stress multiplied by zero point three. Similarly effective adaptation skill becomes base_adaptation multiplied by quantity one minus stress multiplied by zero point three. An architect with base observation skill of zero point eight experiencing stress level zero point six would have effective observation of zero point eight multiplied by quantity one minus zero point one eight, equalling approximately zero point six six. High stress impairs ability to detect subtle behavioural cues and reduces cognitive flexibility for strategy adjustment.

Fatigue Level, ranging from zero (fully rested) to one (exhausted), reduces observation skill by twenty percent and adaptation skill by twenty percent through analogous multiplicative penalties. An architect operating with fatigue level zero point five experiences effective observation of base_observation multiplied by quantity one minus zero point one, retaining ninety percent of base capability. Cumulative fatigue from back-to-back meetings compounds these effects.

Emotional State, ranging from zero (highly negative emotional state) to one (highly positive emotional state), reduces observation skill by twenty percent and self-awareness skill by thirty percent when in negative emotional states. The calculation uses quantity one minus emotional_state to convert the scale such that low emotional state values create high penalties. An architect in negative emotional state (emotional_state equals zero point three) experiences effective observation reduced by fourteen percent and self-awareness reduced by twenty-one percent. Negative emotional states cause inward focus reducing capacity to accurately read others and tendency toward defensiveness reducing self-awareness.

Overconfidence, ranging from zero (appropriately confident) to one (extremely overconfident), reduces self-awareness skill by forty percent. The penalty calculation follows the pattern effective_self_awareness equals base_self_awareness multiplied by quantity one minus overconfidence multiplied by zero point four. An architect with overconfidence level zero point seven retains only seventy-two percent of base self-awareness. Overconfidence creates blind spots preventing recognition of own limitations and biases.

Ego Investment, ranging from zero (emotionally detached from outcome) to one (heavily ego-invested), reduces adaptation skill by thirty percent. High ego investment in being right or winning creates rigidity preventing flexible strategy adjustment. An architect with ego investment level zero point eight retains only seventy-six percent of base adaptation capability.

These confounders combine multiplicatively rather than additively, reflecting compounding effects of multiple stressors. An architect with base observation skill of zero point seven, experiencing stress level zero point four, fatigue level zero point five, and negative emotional state (emotional_state equals zero point four), would have effective observation calculated as:

effective_observation = 0.7 × (1 - 0.4 × 0.3) × (1 - 0.5 × 0.2) × (1 - (1 - 0.4) × 0.2)
                      = 0.7 × 0.88 × 0.9 × 0.88
                      ≈ 0.49

Thus multiple moderate confounders reduce the architect from seventy percent base capability to forty-nine percent effective capability, demonstrating substantial performance degradation requiring either confounder mitigation (stress reduction, rest, emotional regulation) or acknowledgment of temporarily reduced capacity.

### System Architecture Overview

The invention is embodied in a computer system comprising processing hardware (CPU with vector processing capabilities for Monte Carlo simulation), memory storage (RAM for simulation execution, persistent storage for actor profiles and historical data), network communication interfaces (API endpoints for data input/output), and user interface components (web-based visualisation dashboard).

**Figure 1** illustrates the overall system architecture comprising six primary modules: (1) Actor Profile Management Module storing and updating actor representations; (2) Variable Ontology Engine maintaining the five-layer variable structure; (3) Simulation Engine executing Monte Carlo predictions; (4) Outcome Recording Module capturing empirical results; (5) Bayesian Learning Module updating model parameters; and (6) Strategic Analytics Module providing recommendations. Data flows from left to right: actor profile creation → simulation execution → outcome prediction → actual interaction → outcome recording → model updating → refined predictions.

The backend implementation utilises FastAPI framework (Python 3.9+) providing RESTful API endpoints, PostgreSQL relational database (version 13+) for persistent storage with JSONB columns for flexible variable storage, and NumPy/SciPy libraries for numerical computation. The frontend comprises a React single-page application (TypeScript) with real-time WebSocket connections for simulation progress updates and data visualisation using D3.js and Chart.js libraries.

### Five-Layer Variable Ontology

**Figure 2** depicts the hierarchical ontology structure with five primary layers, each containing 5-12 constituent variables, totalling 40+ quantified communication dimensions.

**Cognitive Layer** quantifies intellectual capacities affecting communication:
- Analytical Reasoning (scale 0-100): capacity for logical argument construction and flaw detection
- Abstract Thinking (0-100): ability to conceptualise non-concrete ideas
- Pattern Recognition (0-100): skill in identifying trends and connections
- Knowledge Depth: array of domain expertise levels, e.g., {finance: 80, technology: 65, healthcare: 30}
- Learning Rate (0-10): speed of new concept acquisition
- Cognitive Flexibility (0-100): adaptability in changing argumentative contexts
- Memory Capacity (0-100): retention of conversation details
- Processing Speed (0-100): rapidity of comprehension and response formulation

**Emotional Layer** models affective dimensions:
- Emotional Intelligence (0-100): accuracy in perceiving others' emotional states
- Empathy (0-100): capacity for perspective-taking
- Stress Resilience (0-100): performance maintenance under pressure
- Emotional Stability (0-100): consistency of emotional state
- Optimism Bias (-50 to +50): tendency toward positive/negative expectations
- Emotional Expressiveness (0-100): degree of outward emotional display
- Conflict Tolerance (0-100): comfort with disagreement or tension

**Sociocultural Layer** captures social and cultural influences:
- Cultural Fluency: dictionary mapping cultures to competency scores, e.g., {UK_Business: 90, US_Tech: 70, Japanese_Formal: 40}
- Social Status Sensitivity (0-100): responsiveness to hierarchical cues
- Authority Response Pattern (categorical): {Deferential, Collaborative, Challenging, Independent}
- Group Identity Strength (0-100): degree of in-group affiliation
- Formality Preference (0-100): inclination toward formal vs. casual communication
- Network Centrality (0-100): position within relevant social networks

**Behavioural Layer** quantifies observable communication patterns:
- Communication Style (categorical): {Direct, Indirect, Assertive, Passive, Aggressive}
- Verbosity (0-100): typical word count in responses
- Interruption Tendency (0-100): likelihood of speaking over others
- Question-Asking Frequency (0-100): rate of inquiry during dialogue
- Risk Tolerance (0-100): comfort with uncertain outcomes
- Decision-Making Speed (0-100): rapidity of commitment
- Detail Orientation (0-100): focus on specifics vs. big-picture

**Strategic Layer** models goal-oriented communication:
- Goal Clarity (0-100): specificity of interaction objectives
- Strategic Thinking (0-100): capacity for multi-move planning
- Long-Term Orientation (0-100): weight given to future consequences vs. immediate outcomes
- Negotiation Skill (0-100): effectiveness in value-claiming and value-creation
- Persuasion Competency (0-100): ability to shift others' positions
- Adaptability (0-100): responsiveness to changing interaction dynamics

Each variable is stored as a Beta distribution Beta(α,β) where α and β are shape parameters updated through Bayesian learning. The Beta distribution is selected for technical reasons: (1) bounded support on [0,1] naturally representing percentage scales; (2) flexible shape enabling representation of diverse belief states (uniform, peaked, bimodal); (3) conjugate prior for Bernoulli/Binomial likelihoods enabling closed-form Bayesian updates; and (4) interpretable parameters where α/(α+β) represents the mean and α+β represents certainty (concentration).

### Actor Profile Data Structure

**Figure 3** shows the actor profile schema implemented as a PostgreSQL table with the following structure:

```
TABLE actor_profiles {
  id: UUID PRIMARY KEY,
  name: VARCHAR(255),
  created_at: TIMESTAMP,
  updated_at: TIMESTAMP,
  archetype: ENUM(Analytical_Skeptic, Charismatic_Champion, Pragmatic_Operator, 
                  Empathetic_Collaborator, Strategic_Visionary, Defensive_Guardian),
  variables: JSONB,
  interaction_count: INTEGER,
  last_interaction: TIMESTAMP,
  confidence_score: FLOAT
}
```
