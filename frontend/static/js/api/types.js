// JSDoc mirrors of contracts/schemas (contract v0.2.0, merged at f7cef55).
// The schemas are the source of truth; these typedefs exist for editor checking only.

/**
 * @typedef {Object} Source
 * @property {string} title
 * @property {string} url                 http(s) only
 * @property {string|number|null} [page]
 * @property {string|null} [quote]        Recorded quote. Recorded is not verified (S10d, Q3).
 * @property {string} retrieved           YYYY-MM-DD
 * @property {string|null} [archive_id]
 */

/** @typedef {"measured"|"interpretation"} EvidenceClass */
/** @typedef {"reported"|"not_reported"|"not_applicable"|"excluded"} ValueStatus */
/** @typedef {"spacecraft"|"space_station"|"lunar_base"|"martian_base"|"pressurized_rover"|"earth"} Environment */

/**
 * Every key is present; null means not reported. Units are in the key names.
 * @typedef {Object} Conditions
 * @property {"microgravity"|"partial_gravity"|"normal_gravity"|null} gravity_environment
 * @property {number|null} oxygen_mole_fraction
 * @property {number|null} pressure_kpa
 * @property {number|null} flow_velocity_mm_s
 * @property {"opposed"|"concurrent"|"quiescent"|null} flow_configuration
 * @property {string|null} diluent
 * @property {string|null} fuel_or_material
 * @property {string|null} sample_geometry
 */

/**
 * FlameGuard-SI caution or exclusion on a measured value. Never source text.
 * @typedef {Object} CurationNote
 * @property {"caution"|"exclusion"} kind
 * @property {string} note
 * @property {"FlameGuard-SI"} generated_by
 * @property {{manifest_id: string, flag_id: string}} flag_ref
 * @property {Source} source               with a recorded (not verified) quote
 */

/**
 * @typedef {Object} Investigation
 * @property {boolean} [fixture]
 * @property {string} id
 * @property {string} name
 * @property {string|null} [acronym]
 * @property {string|null} [platform]
 * @property {string[]} [objectives]
 * @property {Environment[]} [relevant_environments]
 * @property {string[]} [datasets]          manifest ids
 * @property {Source[]} sources
 */

/**
 * @typedef {Object} Finding
 * @property {boolean} [fixture]
 * @property {string} id
 * @property {string} investigation_id
 * @property {EvidenceClass} evidence_class
 * @property {string} statement
 * @property {string|null} quantity
 * @property {number|string|null} value
 * @property {string|null} unit
 * @property {ValueStatus} value_status
 * @property {string|null} [uncertainty]    source-reported only
 * @property {Conditions} [conditions]      required on measured
 * @property {string[]} [fire_safety_topics]
 * @property {CurationNote[]} [curation_notes]  measured only
 * @property {Environment[]} [relevant_environments]  interpretation only
 * @property {string[]} [limitations]       interpretation only (required there)
 * @property {Object} provenance            measured: {manifest_id, locator, sources}; interpretation: {derived_from, method, method_version, generated_by}
 */

/**
 * @typedef {Object} ListResponse
 * @property {string} contract_version
 * @property {Array<any>} items
 * @property {number} total
 */

/**
 * @typedef {Object} Comparison
 * @property {boolean} [fixture]
 * @property {string} contract_version
 * @property {string} quantity
 * @property {string} unit
 * @property {Array<{investigation_id: string, finding_id: string, evidence_class: "measured", value: number|null, value_status: ValueStatus, conditions: Conditions}>} rows
 * @property {boolean} comparable          decided by the backend only
 * @property {string[]} non_comparable_reasons
 */

/**
 * @typedef {Object} Ranking
 * @property {boolean} [fixture]
 * @property {string} contract_version
 * @property {Environment} context
 * @property {string} criteria_version
 * @property {Array<{id: string, description: string, weight: number}>} criteria
 * @property {Array<{rank: number, investigation_id: string, score: number, rationale: string, criterion_scores: Array<{criterion_id: string, score: number, inputs: Array<{finding_id: string, evidence_class: EvidenceClass}>}>}>} items
 * @property {Array<{investigation_id: string, reason: string}>} excluded   investigations not ranked
 * @property {"FlameGuard-SI"} generated_by
 */

/**
 * @typedef {Object} AssistantAnswer
 * @property {boolean} [fixture]
 * @property {string} contract_version
 * @property {string} answer
 * @property {"ai"|"fallback_quotes"|"no_evidence"} mode
 * @property {Array<{finding_id: string, evidence_class: EvidenceClass, source: Source}>} citations
 * @property {"FlameGuard-SI"} generated_by
 * @property {string[]} limitations
 */

/**
 * @typedef {Object} SimulationResult
 * @property {boolean} [fixture]
 * @property {string} id
 * @property {"illustrative_simulation"} evidence_class
 * @property {string} label
 * @property {string} model
 * @property {string} model_version
 * @property {"unverified"|"numerically_verified"} [verification_status]
 * @property {Record<string, any>} parameters
 * @property {Record<string, any>} outputs
 */

/**
 * Common interface implemented by the HTTP adapter and the fixture adapter.
 * @typedef {Object} DataSource
 * @property {"api"|"fixtures"} kind
 * @property {string} description
 * @property {() => Promise<{status: string, service: string, contract_version: string}>} health
 * @property {() => Promise<ListResponse>} listInvestigations
 * @property {(id: string) => Promise<Investigation>} getInvestigation
 * @property {(investigationId?: string) => Promise<ListResponse>} listFindings
 * @property {(quantity: string, investigationIds?: string[]) => Promise<Comparison>} compare
 * @property {(context: string) => Promise<Ranking>} getRankings
 * @property {(question: string, investigationIds?: string[]) => Promise<AssistantAnswer>} ask
 * @property {(id: string) => Promise<SimulationResult>} getSimulation
 */

export {};
