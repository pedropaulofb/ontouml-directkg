"""Actual CLI processes, delivery and parity; no executable name is invented."""

import copy
import json
from pathlib import Path

import pytest
import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import fixture_path, fixture_issues, load_json, source_element, source_elements, write_input
from tests.support.invocation import Fault, diagnostic_signatures
from tests.support.rdf import assert_graph_equal, property_chains, rooted_graph

BASE=Namespace('https://example.test/model#')
ONTOLOGY=URIRef('https://example.test/model')
PROV=Namespace('http://www.w3.org/ns/prov#')
METADATA='shared/external_metadata'
POLICIES=['strict','tolerant','best-effort']


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", ["whitespace", "non_utf8", "duplicate"])
def test_cli_opaque_identifier_policy_and_report(invoke, tmp_path, input_policy, condition):
    """Rules: DK-IRI-02, DK-IRI-05, DK-DIAG-04, DK-DIAG-05, DK-CONF-02; §3.4 and §15 exit codes. RD-02 Alternative A."""
    document = load_json("shared/base_iri")
    focus = source_element(document, "C17")
    if condition == "whitespace":
        focus["id"] = "\t\n"
    elif condition == "non_utf8":
        focus["id"] = "\ud800"
    else:
        document["model"]["contents"].append(copy.deepcopy(focus))
    source = write_input(tmp_path, document, ensure_ascii=True)
    destination = tmp_path / "actual.ttl"
    report_path = tmp_path / "actual.json"
    process = invoke.cli(source, options={"base_iri": str(BASE), "iri_strategy": "id",
                                        "provenance": "none", "input_policy": input_policy},
                         workdir=tmp_path, output_path=destination, diagnostics_path=report_path)
    assert process.command and isinstance(process.stdout, bytes) and isinstance(process.stderr, bytes)
    assert report_path.is_file()
    report = invoke.read_report(report_path)
    assert report.raw == json.loads(report_path.read_bytes())
    if condition == "whitespace":
        expected_outcome, expected_code = "completed", 0
    elif condition == "non_utf8" and input_policy == "best-effort":
        expected_outcome, expected_code = "completed-with-errors", 1
    else:
        expected_outcome, expected_code = "aborted", 3
    assert process.returncode == expected_code
    assert process.observation.outcome == expected_outcome
    assert report.outcomes == (expected_outcome,)
    assert diagnostic_signatures(report.diagnostics) == diagnostic_signatures(process.observation.diagnostics)
    if condition == "whitespace":
        graph = Graph().parse(destination, format="turtle")
        assert set(graph.subjects(RDF.type, OWL.Class)) == {BASE._x09_x0A}
        assert not any(d.severity == "ERROR" for d in report.diagnostics)
    else:
        assert any(d.severity == "ERROR" for d in report.diagnostics)
        assert any(event.severity == "ERROR" for event in process.console)
        if expected_outcome == "aborted":
            assert not destination.exists()
            assert process.observation.ontology is None
        else:
            graph = Graph().parse(destination, format="turtle")
            assert not list(graph.subjects(RDF.type, OWL.Class))
        if condition == "duplicate":
            assert any(d.kind == "duplicate_id" for d in report.diagnostics)


DEFAULTS={'iri_strategy':'name','input_policy':'tolerant','stereotype_policy':'allow-custom','inverse_properties':'all',
          'material_property_chains':'none','relation_labels':'source-only','omit_identifiers':False,
          'stereotype_relation_naming':True,'provenance':'embedded'}
CONTROLS=[('--base-iri','base_iri',None),('--iri-strategy','iri_strategy',['name','id']),
          ('--input-policy','input_policy',POLICIES),('--stereotype-policy','stereotype_policy',['require-known','allow-missing','allow-custom']),
          ('--inverse-properties','inverse_properties',['all','informed','named','none']),
          ('--no-stereotype-relation-naming','stereotype_relation_naming',[True,False]),
          ('--relation-labels','relation_labels',['source-only','generated']),
          ('--material-property-chains','material_property_chains',['none','omit-conflicting-constraints','preserve-conflicting-constraints']),
          ('--language','language',None),('--omit-identifiers','omit_identifiers',[True,False]),
          ('--metadata-file','metadata_file',None),('--provenance','provenance',['none','embedded','sidecar'])]
LOGICAL={RDF.type,RDF.first,RDF.rest,RDFS.subClassOf,RDFS.subPropertyOf,RDFS.domain,RDFS.range,RDFS.label,DCTERMS.identifier,
         OWL.onProperty,OWL.cardinality,OWL.minCardinality,OWL.maxCardinality,OWL.onClass,OWL.onDataRange,
         OWL.qualifiedCardinality,OWL.minQualifiedCardinality,OWL.maxQualifiedCardinality,OWL.someValuesFrom,OWL.allValuesFrom,
         OWL.unionOf,OWL.intersectionOf,OWL.oneOf,OWL.disjointUnionOf,OWL.disjointWith,OWL.propertyDisjointWith,
         OWL.inverseOf,OWL.propertyChainAxiom,OWL.equivalentClass,OWL.equivalentProperty,OWL.members,OWL.distinctMembers}


def _report(invoke,path,result):
    report=invoke.read_report(path)
    assert report.raw==json.loads(path.read_bytes()) and report.schema is not None
    assert report.outcomes==(result.outcome,)
    assert diagnostic_signatures(report.diagnostics)==diagnostic_signatures(result.diagnostics)
    return report


def _source(tmp_path,scenario):
    document=load_json('shared/binary_relation' if scenario=='partial' else 'shared/instantiation' if scenario=='instantiation' else 'shared/base_iri')
    options={'base_iri':str(BASE),'iri_strategy':'id','provenance':'none'};faults=()
    if scenario=='warning':source_element(document,'C17')['name']=None;options['iri_strategy']='name'
    elif scenario=='info':source_element(document,'C17').update(isDerived=True,isExtensional=True)
    elif scenario=='partial':source_element(document,'tFocus')['propertyType']=None;options['input_policy']='best-effort'
    elif scenario=='duplicate_abort':document['model']['contents'].append(copy.deepcopy(source_element(document,'C17')))
    elif scenario=='unprocess':
        path=tmp_path/'input.json';path.write_bytes(b'{"id":');return path,options,faults
    elif scenario=='provenance_abort':options['provenance']='embedded';faults=(Fault('provenance','construct'),)
    elif scenario=='singleton':
        child=copy.deepcopy(source_element(document,'C17'));child.update(id='cChild',name='Child')
        document['model']['contents'] += [child,
            {'id':'gChild','name':None,'description':None,'type':'Generalization','propertyAssignments':None,
             'specific':{'id':'cChild','type':'Class'},'general':{'id':'C17','type':'Class'}},
            {'id':'gsSingleton','name':None,'description':None,'type':'GeneralizationSet','propertyAssignments':None,
             'generalizations':[{'id':'gChild','type':'Generalization'}],'isDisjoint':False,'isComplete':True,'categorizer':None}]
    return write_input(tmp_path,document),options,faults


def _assert_process(process):
    assert process.command and isinstance(process.stdout,bytes) and isinstance(process.stderr,bytes)
    assert process.conversion_started is True


def _failed(result,kind,destination):
    failures=[failure for failure in result.delivery_failures if failure.kind==kind]
    assert failures and all(failure.destination==destination and failure.reason and failure.raw is not None for failure in failures)
    assert any(d.kind==kind+'_delivery' and d.severity=='ERROR' for d in result.diagnostics)
    assert result.valid_artifacts is not None and destination not in result.valid_artifacts
    return failures


@pytest.mark.parametrize('flag,semantic,choices',CONTROLS,ids=[row[1] for row in CONTROLS])
def test_cli_and_python_expose_all_established_controls_values_and_defaults(invoke,flag,semantic,choices):
    """Rules: DK-INV-01, DK-REL-04, DK-REL-07, DK-LBL-01, DK-LBL-02, DK-IRI-01, DK-IRI-02, DK-IRI-09, DK-GEN-09, DK-GEN-10, DK-DIAG-05, DK-DIAG-06. Also §§2.2/15 parity."""
    surface=invoke.inspect_controls();cli=surface.cli[flag];python=surface.python[semantic]
    assert cli.raw is not None and python.raw is not None and surface.raw is not None
    assert cli.parameter==flag
    if choices is not None:assert set(cli.choices)==set(python.choices)==set(choices)
    if semantic in DEFAULTS:assert cli.default==python.default==DEFAULTS[semantic]
    if semantic=='relation_labels':assert python.parameter=='relation_labels'
    if semantic=='language':assert cli.arity==1


@pytest.mark.parametrize('flag,choices,default',[('--console-level',['info','warning','error'],'info'),('--diagnostics-file',None,None)],ids=['console_level','diagnostics_file'])
def test_cli_delivery_and_presentation_controls_are_inspected_without_inventing_python_parameters(invoke,flag,choices,default):
    """Rules: DK-DIAG-04. Also §15 controls."""
    control=invoke.inspect_controls().cli[flag]
    assert control.parameter==flag and control.raw is not None
    if choices is not None:assert set(control.choices)==set(choices) and control.default==default


@pytest.mark.parametrize('feature',['ontology_iri','local_value_restrictions','omit_reverse_cardinalities','qualified_relation_cardinalities'])
@pytest.mark.parametrize('interface',['cli','python'])
def test_unestablished_semantic_shortcuts_are_not_exposed(invoke,feature,interface):
    """Rules: DK-IRI-01, DK-ATT-04, DK-REL-09, DK-REL-10. Also §15 configuration boundary."""
    assert invoke.inspect_controls().prohibited_features[interface+':'+feature] is False


PARITY_CASES=[('iri_strategy',v) for v in ('name','id')]+[('input_policy',v) for v in POLICIES]+[
    ('stereotype_policy',v) for v in ('require-known','allow-missing','allow-custom')]+[
    ('inverse_properties',v) for v in ('all','informed','named','none')]+[
    ('stereotype_relation_naming',v) for v in (True,False)]+[('relation_labels',v) for v in ('source-only','generated')]+[
    ('material_property_chains',v) for v in ('none','omit-conflicting-constraints','preserve-conflicting-constraints')]+[
    ('language','fr'),('omit_identifiers',False),('omit_identifiers',True),('metadata_file','selected')]+[
    ('provenance',v) for v in ('none','embedded','sidecar')]+[
    ('base_iri',v) for v in ('https://example.test/other#','https://example.test/other/','urn:directkg:test:')]


@pytest.mark.parametrize('control,value',PARITY_CASES,ids=[control+'_'+str(value).replace('/','_') for control,value in PARITY_CASES])
def test_equivalent_cli_and_python_controls_preserve_scoped_mapping_identity_and_lists(invoke,tmp_path,control,value):
    """Rules: DK-INV-01, DK-REL-04, DK-REL-07, DK-LBL-01, DK-LBL-02, DK-IRI-01, DK-IRI-02, DK-IRI-09, DK-GEN-09, DK-GEN-10, DK-DIAG-04, DK-DIAG-05, DK-DIAG-06, DK-CONF-01. Also §§2.2/3.3/15 parity."""
    key='shared/material_pattern' if control=='material_property_chains' else 'shared/binary_relation' if control in {'inverse_properties','stereotype_relation_naming','relation_labels'} else 'shared/base_iri'
    document=load_json(key);options={'base_iri':str(BASE),'iri_strategy':'id','provenance':'none'}
    options[control]=fixture_path(METADATA,'metadata.yaml') if control=='metadata_file' else value
    if control=='input_policy':source_element(document,'C17')['unknownCLIInformation']='UNRECOGNIZED'
    elif control=='stereotype_policy':source_element(document,'C17')['stereotype']='unrecognizedCustomStereotype'
    elif control=='inverse_properties':
        source_element(document,'sFocus')['name']='workers' if value in {'named','none'} else None
        source_element(document,'sFocus')['cardinality']=None if value in {'named','all'} else '1'
    elif control in {'stereotype_relation_naming','relation_labels'}:
        source_element(document,'rFocus').update(name=None,stereotype='bringsAbout')
        source_element(document,'tFocus')['name']=None
        source_element(document,'cA')['stereotype']='event';source_element(document,'cB')['stereotype']='situation'
        if control=='stereotype_relation_naming':options['iri_strategy']='name'
    elif control=='omit_identifiers':options['iri_strategy']='name'
    elif control=='language':
        document.update(name='Project Text',languages=['nl'])
        source_element(document,'C17')['name']={'en':'Person','pt':'Pessoa'}
    source=write_input(tmp_path,document);destination=tmp_path/'actual.ttl';report_path=tmp_path/'actual.report'
    python=invoke.convert(source,options=options,workdir=tmp_path)
    process=invoke.cli(source,options=options,workdir=tmp_path,output_path=destination,diagnostics_path=report_path)
    _assert_process(process);cli=process.observation
    assert cli.outcome==python.outcome
    assert process.returncode=={'completed':0,'completed-with-errors':1,'aborted':3}[python.outcome]
    assert diagnostic_signatures(cli.diagnostics)==diagnostic_signatures(python.diagnostics)
    _report(invoke,report_path,cli)
    if python.outcome=='aborted':assert cli.ontology is None and not destination.exists();return
    actual=Graph().parse(destination,format='turtle')
    base=str(options['base_iri']);base=base if base.endswith(('#','/')) else base+'#'
    namespace=Namespace(base);ontology=URIRef(base[:-1] if base.endswith('#') else base)
    if options['iri_strategy']=='id':roots={namespace[element['id']] for element in source_elements(document)}
    elif control=='omit_identifiers':roots={namespace.Person}
    else:
        ids={element['id'] for element in source_elements(document)}
        mapping=lambda graph:{identifier:frozenset(graph.subjects(DCTERMS.identifier,Literal(identifier))) for identifier in ids}
        assert mapping(python.ontology)==mapping(actual)
        roots=set().union(*mapping(actual).values());assert roots
    roots.add(ontology)
    types={OWL.Class,OWL.ObjectProperty,OWL.DatatypeProperty,OWL.NamedIndividual,OWL.Restriction,OWL.Ontology,OWL.AsymmetricProperty,OWL.AllDifferent}|roots
    projected=lambda graph:rooted_graph(graph,roots,LOGICAL,type_objects=types,unordered_predicates={OWL.disjointWith,OWL.propertyDisjointWith})
    assert_graph_equal(projected(actual),projected(python.ontology))
    if control=='material_property_chains':
        assert property_chains(actual,BASE.tMaterial)==({(('inverse',BASE.tLeft),BASE.tRight)} if value!='none' else set())
    if control=='language':assert (BASE.C17,RDFS.label,Literal('Person',lang='fr')) in actual
    if control=='omit_identifiers':assert ((BASE.Person,DCTERMS.identifier,Literal('C17')) in actual)==(not value)
    if control=='metadata_file':
        assert (ontology,DCTERMS.title,Literal('External Ontology Title')) in actual
    if control=='provenance':
        if value=='none':assert cli.transformation_provenance_output==()
        elif value=='embedded':assert list(actual.objects(ontology,PROV.wasGeneratedBy)) and cli.embedded_output_configuration==()
        else:
            sidecar=destination.with_name(destination.stem+'.provenance.ttl')
            assert sidecar.is_file() and len(Graph().parse(sidecar,format='turtle'))>0


def test_cli_default_controls_match_python_defaults_and_record_effective_configuration(invoke,tmp_path):
    """Rules: DK-GEN-10, DK-IRI-02, DK-INV-01, DK-REL-07, DK-LBL-01, DK-DIAG-04, DK-DIAG-05, DK-DIAG-06. Also §15 defaults/parity."""
    source=fixture_path('shared/base_iri');destination=tmp_path/'defaults.ttl';report=tmp_path/'defaults.json'
    python=invoke.convert(source,options={'base_iri':str(BASE)},workdir=tmp_path)
    process=invoke.cli(source,options={'base_iri':str(BASE)},workdir=tmp_path,output_path=destination,diagnostics_path=report)
    _assert_process(process);assert process.returncode==0 and process.observation.outcome=='completed'
    for observed in (python,process.observation):
        assert observed.configuration_controls is not None
        for key,value in {**DEFAULTS,'base_iri':str(BASE)}.items():assert observed.configuration_controls[key]==value
        assert observed.provenance_roles is not None and observed.provenance_roles.get('configuration')
        config=observed.provenance_roles['configuration'][0]
        assert isinstance(observed.configuration_literal,Literal) and isinstance(yaml.safe_load(str(observed.configuration_literal)),dict)
        assert (config,PROV.value,observed.configuration_literal) in observed.ontology
        assert list(observed.ontology.objects(config,DCTERMS.format)) and observed.configuration_format=='yaml'
    assert (BASE.Person,RDF.type,OWL.Class) in Graph().parse(destination,format='turtle')
    assert process.observation.embedded_output_configuration==()
    assert diagnostic_signatures(process.console)==diagnostic_signatures(process.observation.diagnostics)
    _report(invoke,report,process.observation)


@pytest.mark.parametrize('scenario',['info','warning','singleton','instantiation','partial','duplicate_abort','unprocess','provenance_abort'])
def test_cli_exit_outcome_and_json_mirror_cover_success_recovery_abort_and_loss_notices(invoke,tmp_path,scenario):
    """Rules: DK-DIAG-04, DK-DIAG-05, DK-DIAG-14, DK-DIAG-15, DK-DIAG-16, DK-DIAG-17, DK-INS-02, DK-GEN-10. Also §15 exits."""
    source,options,faults=_source(tmp_path,scenario);destination=tmp_path/'out.ttl';path=tmp_path/'exact-name.reportdata'
    process=invoke.cli(source,options=options,workdir=tmp_path,output_path=destination,diagnostics_path=path,faults=faults)
    _assert_process(process);result=process.observation
    expected='completed-with-errors' if scenario=='partial' else 'aborted' if scenario in {'duplicate_abort','unprocess','provenance_abort'} else 'completed'
    assert result.outcome==expected and process.returncode=={'completed':0,'completed-with-errors':1,'aborted':3}[expected]
    report=_report(invoke,path,result)
    assert diagnostic_signatures(process.console)==diagnostic_signatures(report.diagnostics)
    if expected=='aborted':assert not destination.exists() and result.ontology is None
    else:assert destination.is_file() and len(Graph().parse(destination,format='turtle'))>0
    if scenario=='info':
        assert {'abstractness','derived_status','extensionality'}<={d.kind for d in report.diagnostics if d.severity=='INFO'}
    elif scenario=='singleton':assert any(d.kind=='singleton_completeness' and d.severity=='INFO' for d in report.diagnostics)
    elif scenario=='instantiation':
        warnings=[d for d in report.diagnostics if d.kind=='discarded_instantiation_data']
        assert len(warnings)==1 and warnings[0].severity=='WARNING' and 'rInstantiation' in warnings[0].source_ids
        assert result.discarded_instantiation_output==()
        assert 'DISCARDED_' not in path.read_text() and '37..41' not in path.read_text() and '43..47' not in path.read_text()
    elif scenario=='partial':assert any(d.severity=='ERROR' for d in report.diagnostics)


@pytest.mark.parametrize('level',['info','warning','error'])
@pytest.mark.parametrize('scenario',['info','warning','partial','duplicate_abort'])
def test_console_threshold_filters_only_display_and_keeps_reports_outcomes_exit_and_graph(invoke,tmp_path,level,scenario):
    """Rules: DK-DIAG-04, DK-DIAG-05, DK-IRI-04. Also §15 console levels."""
    source,options,faults=_source(tmp_path,scenario)
    observations=[]
    for selected in ('info',level):
        directory=tmp_path/('baseline' if not observations else 'selected');directory.mkdir()
        process=invoke.cli(source,options={**options,'console_level':selected},workdir=directory,output_path=directory/'out.ttl',diagnostics_path=directory/'report.json',faults=faults)
        _assert_process(process);_report(invoke,directory/'report.json',process.observation);observations.append(process)
    first,second=observations
    assert first.returncode==second.returncode and first.observation.outcome==second.observation.outcome
    assert diagnostic_signatures(first.observation.diagnostics)==diagnostic_signatures(second.observation.diagnostics)
    allowed={'INFO','WARNING','ERROR'} if level=='info' else {'WARNING','ERROR'} if level=='warning' else {'ERROR'}
    assert diagnostic_signatures(second.console)==diagnostic_signatures([d for d in second.observation.diagnostics if d.severity in allowed])
    class_iri=BASE.unnamedClass_C17 if scenario=='warning' else BASE.C17
    if scenario=='warning':
        for observed in (first.observation,second.observation):
            assert observed.ontology is not None
            assert (class_iri,RDF.type,OWL.Class) in observed.ontology
    if first.observation.ontology is None:assert second.observation.ontology is None
    else:
        roots={class_iri,BASE.cA,BASE.cB,BASE.tFocus,BASE.sFocus,ONTOLOGY}
        types={OWL.Class,OWL.ObjectProperty,OWL.Restriction,OWL.Ontology}
        projection=lambda g:rooted_graph(g,roots,LOGICAL,type_objects=types)
        assert_graph_equal(projection(first.observation.ontology),projection(second.observation.ontology))


def test_cli_creates_no_diagnostics_report_when_option_is_absent(invoke,tmp_path):
    """Rules: DK-DIAG-04."""
    source,options,_=_source(tmp_path,'warning')
    process=invoke.cli(source,options=options,workdir=tmp_path,output_path=tmp_path/'out.ttl')
    assert process.returncode==0 and process.observation.diagnostics_exports==()
    assert any(d.severity=='WARNING' for d in process.console)


@pytest.mark.parametrize('scenario',['info','partial','duplicate_abort'])
def test_cli_and_separate_python_exports_use_the_same_real_schema_and_event_content(invoke,tmp_path,scenario):
    """Rules: DK-DIAG-04, DK-DIAG-05. Also §15 Python export/parity."""
    source,options,faults=_source(tmp_path,scenario)
    python=invoke.convert(source,options=options,workdir=tmp_path,faults=faults)
    python_path=tmp_path/'python.json';cli_path=tmp_path/'cli.json'
    assert invoke.export_diagnostics(python,python_path).failure is None
    process=invoke.cli(source,options=options,workdir=tmp_path,output_path=tmp_path/'out.ttl',diagnostics_path=cli_path,faults=faults)
    left=_report(invoke,python_path,python);right=_report(invoke,cli_path,process.observation)
    assert left.schema==right.schema
    assert left.outcomes==right.outcomes
    assert diagnostic_signatures(left.diagnostics)==diagnostic_signatures(right.diagnostics)


INVALID_ARGS=[('--unknown-directkg-option',),('--iri-strategy','INVALID'),('--input-policy','INVALID'),
              ('--stereotype-policy','INVALID'),('--inverse-properties','INVALID'),('--relation-labels','INVALID'),
              ('--material-property-chains',),('--material-property-chains','INVALID'),('--provenance','INVALID'),('--language',)]
@pytest.mark.parametrize('arguments',INVALID_ARGS,ids=['unknown_option','iri_value','policy_value','stereotype_value','inverse_value','labels_value','old_boolean_chains','chains_value','provenance_value','missing_language'])
def test_invalid_cli_invocation_has_no_conversion_outcome_or_ontology(invoke,tmp_path,arguments):
    """Rules: DK-DIAG-04, DK-DIAG-05. Also §15 invalid invocation.

    Generic argument errors do not prescribe report-file behavior. Supplied-base
    rejection has its own explicit report prohibition, checked separately.
    """
    destination=tmp_path/'out.ttl';report=tmp_path/'report.json'
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE)},workdir=tmp_path,output_path=destination,diagnostics_path=report,extra_args=arguments)
    assert process.returncode==2 and process.conversion_started is False
    assert process.observation.outcome is None and process.observation.ontology is None
    assert not destination.exists()
    assert process.stdout or process.stderr


@pytest.mark.parametrize('base',['','relative/path','https://example.test/has space'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_supplied_base_rejection_precedes_conversion_and_requested_reporting(invoke,tmp_path,base,input_policy):
    """Rules: DK-IRI-01, DK-DIAG-04, DK-DIAG-05. Also §15 invalid supplied base."""
    destination=tmp_path/'out.ttl';report=tmp_path/'report.json'
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':base,'input_policy':input_policy},workdir=tmp_path,output_path=destination,diagnostics_path=report)
    assert process.returncode==2 and process.conversion_started is False
    assert process.observation.outcome is None and process.observation.ontology is None
    assert not destination.exists() and not report.exists()


@pytest.mark.parametrize('variant',['metadata.yaml','metadata/ignored/metadata.yaml','metadata/nulls/metadata.yaml','metadata/empties/metadata.yaml','metadata/empty_mapping/metadata.yaml','metadata/root_list/metadata.yaml','metadata/partial_invalid/metadata.yaml'],ids=['selected','ignored','nulls','empties','empty_mapping','root_list','partial_invalid'])
def test_cli_external_metadata_uses_shared_inputs_and_governed_best_effort_recovery(invoke,tmp_path,variant):
    """Rules: DK-GEN-09, DK-DIAG-04, DK-DIAG-05."""
    path=fixture_path(METADATA,variant);destination=tmp_path/'out.ttl';report=tmp_path/'report.json'
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'metadata_file':path,'provenance':'none','input_policy':'best-effort'},workdir=tmp_path,output_path=destination,diagnostics_path=report)
    result=process.observation;bad=any(s in variant for s in ('root_list','partial_invalid'))
    assert process.returncode==(1 if bad else 0)
    assert result.outcome==('completed-with-errors' if bad else 'completed')
    _report(invoke,report,result)
    assert (BASE.Person,RDF.type,OWL.Class) in Graph().parse(destination,format='turtle')
    if any(s in variant for s in ('root_list','nulls','empties','empty_mapping')):assert result.external_metadata_output==()
    elif 'partial_invalid' in variant:assert (ONTOLOGY,DCTERMS.title,Literal('Kept Valid Title')) in result.ontology
    elif 'ignored' in variant:assert not any(d.kind=='metadata_field' for d in result.diagnostics)
    else:assert (ONTOLOGY,DCTERMS.title,Literal('External Ontology Title')) in result.ontology


@pytest.mark.parametrize('policy,scenario',[(p,'info') for p in POLICIES]+[('best-effort','partial')],ids=['strict_completed','tolerant_completed','best_effort_completed','best_effort_partial'])
@pytest.mark.parametrize('failed',[(d,o,s) for d in (False,True) for o in (False,True) for s in (False,True) if d or o or s],ids=['diag'+str(int(d))+'_ontology'+str(int(o))+'_sidecar'+str(int(s)) for d in (False,True) for o in (False,True) for s in (False,True) if d or o or s])
def test_delivery_failure_precedence_keeps_transformation_outcome_and_eligible_outputs(invoke,tmp_path,policy,scenario,failed):
    """Rules: DK-DIAG-04, DK-DIAG-05, DK-GEN-10. Also §15 codes 4/6/5 precedence."""
    diagnostics_failed,ontology_failed,sidecar_failed=failed
    source,options,_=_source(tmp_path,scenario);options.update(input_policy=policy,provenance='sidecar')
    destination=tmp_path/'out.ttl';report=tmp_path/'report.json';sidecar=tmp_path/'out.provenance.ttl'
    faults=tuple(Fault(kind,'write',path) for flag,kind,path in [(diagnostics_failed,'diagnostics',report),(ontology_failed,'ontology',destination),(sidecar_failed,'sidecar',sidecar)] if flag)
    process=invoke.cli(source,options=options,workdir=tmp_path,output_path=destination,diagnostics_path=report,faults=faults)
    _assert_process(process);result=process.observation
    assert process.returncode==(4 if diagnostics_failed else 6 if ontology_failed else 5)
    assert result.outcome==('completed-with-errors' if scenario=='partial' else 'completed')
    if diagnostics_failed:
        failures=[f for f in result.delivery_failures if f.kind=='diagnostics']
        assert failures and all(f.destination==report and f.reason and f.raw is not None for f in failures)
        assert any(d.kind=='diagnostics_delivery' and d.severity=='ERROR' for d in process.console)
    else:_report(invoke,report,result)
    if ontology_failed:
        _failed(result,'ontology',destination)
        assert not sidecar.exists()
        assert not any(op.kind=='sidecar' and op.operation in {'create','write'} for op in result.operations or ())
    else:
        assert destination.is_file() and len(Graph().parse(destination,format='turtle'))>0
        if sidecar_failed:_failed(result,'sidecar',sidecar)
        else:assert sidecar.is_file() and len(Graph().parse(sidecar,format='turtle'))>0
    for flag,kind in [(diagnostics_failed,'diagnostics'),(ontology_failed,'ontology'),(sidecar_failed and not ontology_failed,'sidecar')]:
        if flag:assert any(op.kind==kind and op.failed and op.raw is not None for op in result.operations or ())


@pytest.mark.parametrize('kind,operation',[('ontology','create'),('ontology','write'),('sidecar','serialize'),('sidecar','create'),('sidecar','write')],ids=['ontology_create','ontology_write','sidecar_serialize','sidecar_create','sidecar_write'])
@pytest.mark.parametrize('old_file',[False,True],ids=['new_destination','old_destination'])
def test_cli_failed_artifacts_are_not_presented_as_valid_and_retained_old_files_are_reported(invoke,tmp_path,kind,operation,old_file):
    """Rules: DK-DIAG-04, DK-GEN-10. Also §15 codes 5/6."""
    destination=tmp_path/'out.ttl';sidecar=tmp_path/'out.provenance.ttl';report=tmp_path/'report.json'
    path=destination if kind=='ontology' else sidecar
    if old_file:path.write_bytes(b'OLD_ARTIFACT')
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'sidecar'},workdir=tmp_path,output_path=destination,diagnostics_path=report,faults=(Fault(kind,operation,path),))
    assert process.returncode==(6 if kind=='ontology' else 5) and process.observation.outcome=='completed'
    result=process.observation;failures=_failed(result,kind,path)
    _report(invoke,report,result)
    assert any(op.kind==kind and op.operation==operation and op.failed and op.raw is not None for op in result.operations or ())
    if old_file and path.exists() and path.read_bytes()==b'OLD_ARTIFACT':assert all(f.old_file_not_updated for f in failures)
    assert any(d.kind==kind+'_delivery' and d.severity=='ERROR' for d in process.console)
    if kind=='ontology':assert not sidecar.exists()
    else:assert len(Graph().parse(destination,format='turtle'))>0


@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('operation',['create','write'])
def test_diagnostics_failure_after_duplicate_abort_retains_both_failures_and_code_four(invoke,tmp_path,input_policy,operation):
    """Rules: DK-DIAG-04, DK-DIAG-05. Also §15 code 4 over 3."""
    source,options,_=_source(tmp_path,'duplicate_abort');options['input_policy']=input_policy
    report=tmp_path/'report.json';destination=tmp_path/'out.ttl'
    process=invoke.cli(source,options=options,workdir=tmp_path,output_path=destination,diagnostics_path=report,faults=(Fault('diagnostics',operation,report),))
    assert process.returncode==4 and process.observation.outcome=='aborted'
    assert process.observation.ontology is None and not destination.exists()
    assert any(d.kind=='duplicate_id' and d.severity=='ERROR' for d in process.observation.diagnostics)
    assert any(d.kind=='diagnostics_delivery' and d.severity=='ERROR' for d in process.console)


@pytest.mark.parametrize('mode',['embedded','sidecar'])
@pytest.mark.parametrize('policy',POLICIES)
@pytest.mark.parametrize('report_failure',[False,True],ids=['report_written','report_failure'])
def test_required_provenance_construction_failure_aborts_before_cli_ontology_delivery(invoke,tmp_path,mode,policy,report_failure):
    """Rules: DK-GEN-10, DK-DIAG-04, DK-DIAG-05. Also §15 codes 3/4."""
    report=tmp_path/'report.json';destination=tmp_path/'out.ttl'
    faults=(Fault('provenance','construct'),)+((Fault('diagnostics','write',report),) if report_failure else ())
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':mode,'input_policy':policy},workdir=tmp_path,output_path=destination,diagnostics_path=report,faults=faults)
    assert process.returncode==(4 if report_failure else 3)
    assert process.observation.outcome=='aborted' and process.observation.ontology is None
    assert not destination.exists() and not (tmp_path/'out.provenance.ttl').exists()
    assert any(d.kind=='required_provenance' and d.severity=='ERROR' for d in process.observation.diagnostics)
    if not report_failure:_report(invoke,report,process.observation)


def test_stdout_sidecar_request_never_invents_an_automatic_sidecar_filename(invoke,tmp_path):
    """Rules: DK-GEN-10. Conditional stdout form; §15 invocation."""
    supported=invoke.inspect_controls().stdout_supported
    assert supported is not None, 'Inspect actual stream capability; do not invent CLI syntax'
    if not supported:return
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'sidecar'},workdir=tmp_path)
    assert process.observation.sidecar_writes==()
    assert not list(tmp_path.glob('*.provenance.ttl'))
    if process.conversion_started:
        assert process.observation.outcome in {'completed','completed-with-errors','aborted'}
    else:assert process.returncode==2 and process.observation.outcome is None


@pytest.mark.parametrize('filename',['hospital.ttl','hospital.part.ttl','without_extension'])
def test_cli_sidecar_names_and_final_ontology_byte_digest_are_observed(invoke,tmp_path,filename):
    """Rules: DK-GEN-10. Also §3.3 serialization."""
    import hashlib
    spdx=Namespace('http://spdx.org/rdf/terms#')
    destination=tmp_path/filename
    metadata=fixture_path(METADATA,'metadata.yaml')
    source=fixture_path('shared/base_iri')
    process=invoke.cli(source,options={'base_iri':str(BASE),'provenance':'sidecar','metadata_file':metadata},workdir=tmp_path,output_path=destination,diagnostics_path=tmp_path/'report.json')
    assert process.returncode==0
    sidecar=destination.with_name(destination.stem+'.provenance.ttl')
    assert sidecar.is_file()
    graph=Graph().parse(sidecar,format='turtle');result=process.observation
    assert result.provenance_roles is not None and result.provenance_roles.get('output')
    output=result.provenance_roles['output'][0]
    assert (output,DCTERMS.isFormatOf,ONTOLOGY) in graph and (output,RDF.type,PROV.Entity) in graph
    assert list(graph.objects(output,PROV.wasGeneratedBy))
    assert result.output_filename and Path(result.output_filename).name==filename and result.output_format=='turtle'
    assert result.output_artifact_evidence and all(triple in graph for triple in result.output_artifact_evidence)
    checksums=[node for node in graph.objects(output,spdx.checksum) if (node,spdx.algorithm,spdx.checksumAlgorithm_sha256) in graph]
    assert checksums
    expected=hashlib.sha256(destination.read_bytes()).hexdigest()
    for node in checksums:assert {str(value).lower() for value in graph.objects(node,spdx.checksumValue)}=={expected}
    assert not list(result.ontology.objects(ONTOLOGY,PROV.wasGeneratedBy))
    assert (ONTOLOGY,DCTERMS.title,Literal('External Ontology Title')) in result.ontology
    for role,path in [('source',source),('metadata',metadata)]:
        entity=result.provenance_roles[role][0]
        assert list(graph.subjects(PROV.used,entity))
        digests=[node for node in graph.objects(entity,spdx.checksum) if (node,spdx.algorithm,spdx.checksumAlgorithm_sha256) in graph]
        assert digests
        for node in digests:assert {str(value).lower() for value in graph.objects(node,spdx.checksumValue)}=={hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.mark.parametrize('failure',['missing','permission','malformed','root_list'])
@pytest.mark.parametrize('policy',POLICIES)
@pytest.mark.parametrize('report_failure',[False,True],ids=['report_written','report_failure'])
def test_cli_metadata_file_failures_follow_policy_and_report_delivery_precedence(invoke,tmp_path,failure,policy,report_failure):
    """Rules: DK-GEN-09, DK-GEN-10, DK-DIAG-04, DK-DIAG-05. Also §15 codes 1/3/4."""
    metadata=tmp_path/'metadata.yaml';report=tmp_path/'report.json';destination=tmp_path/'out.ttl';faults=()
    if failure=='permission':metadata.write_text('title: NOT_INGESTED');faults=(Fault('metadata','read',metadata),)
    elif failure=='malformed':metadata.write_text('title: NOT_INGESTED\nlicense: [')
    elif failure=='root_list':metadata.write_bytes(fixture_path(METADATA,'metadata/root_list/metadata.yaml').read_bytes())
    if report_failure:faults+=(Fault('diagnostics','write',report),)
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'embedded','metadata_file':metadata,'input_policy':policy},workdir=tmp_path,output_path=destination,diagnostics_path=report,faults=faults)
    expected='completed-with-errors' if policy=='best-effort' else 'aborted'
    assert process.observation.outcome==expected
    assert process.returncode==(4 if report_failure else 1 if policy=='best-effort' else 3)
    assert any(d.kind=='metadata_input' and d.severity=='ERROR' for d in process.observation.diagnostics)
    if not report_failure:_report(invoke,report,process.observation)
    if policy=='best-effort':
        assert (BASE.Person,RDF.type,OWL.Class) in Graph().parse(destination,format='turtle')
        assert process.observation.external_metadata_output==()
        assert process.observation.provenance_roles is not None
        if failure in {'missing','permission','malformed'}:
            assert not process.observation.provenance_roles.get('metadata',())
    else:assert process.observation.ontology is None and not destination.exists()


def test_absent_base_uses_the_same_placeholder_and_nonfatal_notice_in_both_interfaces(invoke,tmp_path):
    """Rules: DK-IRI-01, DK-DIAG-01, DK-DIAG-04. Also §15 defaults/parity."""
    options={'provenance':'none'};source=fixture_path('shared/base_iri')
    python=invoke.convert(source,options=options,workdir=tmp_path)
    destination=tmp_path/'out.ttl'
    cli=invoke.cli(source,options=options,workdir=tmp_path,output_path=destination,diagnostics_path=tmp_path/'report.json')
    assert cli.returncode==0 and cli.observation.outcome==python.outcome=='completed'
    for result in (python,cli.observation):
        assert (URIRef('https://example.org/directkg'),RDF.type,OWL.Ontology) in result.ontology
        assert (URIRef('https://example.org/directkg#Person'),RDF.type,OWL.Class) in result.ontology
        notices=[d for d in result.diagnostics if d.kind=='placeholder_base']
        assert notices and all(d.severity=='WARNING' for d in notices)
        assert {'placeholder_namespace','not_recommended_for_publication'}<=set().union(*(d.facts for d in notices))


@pytest.mark.parametrize('inverse_mode',['all','none'])
@pytest.mark.parametrize('chain_mode',['omit-conflicting-constraints','preserve-conflicting-constraints'])
def test_cli_chain_order_stays_anonymous_backwards_independently_of_named_inverse_mode(invoke,tmp_path,inverse_mode,chain_mode):
    """Rules: DK-REL-07, DK-INV-01, DK-INV-04, DK-DIAG-07. Also §§3.3/15 parity."""
    destination=tmp_path/'chain.ttl'
    process=invoke.cli(fixture_path('shared/material_pattern'),options={'base_iri':str(BASE),'provenance':'none','iri_strategy':'id','inverse_properties':inverse_mode,'material_property_chains':chain_mode},workdir=tmp_path,output_path=destination,diagnostics_path=tmp_path/'report.json')
    assert process.returncode==0
    graph=Graph().parse(destination,format='turtle')
    assert property_chains(graph,BASE.tMaterial)=={(('inverse',BASE.tLeft),BASE.tRight)}
    assert ((BASE.sLeft,RDF.type,OWL.ObjectProperty) in graph)==(inverse_mode=='all')
    assert any(d.kind=='chain_compatibility' for d in process.observation.diagnostics)
    _report(invoke,tmp_path/'report.json',process.observation)


def test_cli_identifier_opt_out_is_an_accepted_noop_under_id_strategy(invoke,tmp_path):
    """Rules: DK-IRI-02, DK-IRI-09. Also §15 parity."""
    graphs=[]
    for omit in (False,True):
        destination=tmp_path/('optout.ttl' if omit else 'default.ttl')
        process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'none','iri_strategy':'id','omit_identifiers':omit},workdir=tmp_path,output_path=destination)
        assert process.returncode==0
        graph=Graph().parse(destination,format='turtle');graphs.append(graph)
        assert (BASE.C17,RDF.type,OWL.Class) in graph
        assert (BASE.C17,DCTERMS.identifier,Literal('C17')) not in graph
    projection=lambda graph:rooted_graph(graph,{BASE.C17,ONTOLOGY},LOGICAL,type_objects={OWL.Class,OWL.Ontology})
    assert_graph_equal(projection(graphs[0]),projection(graphs[1]))


def test_cli_none_does_not_run_provenance_only_operations(invoke,tmp_path):
    """Rules: DK-GEN-10. Also §15 provenance control."""
    destination=tmp_path/'none.ttl'
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'none'},workdir=tmp_path,output_path=destination,faults=(Fault('provenance','construct'),))
    assert process.returncode==0 and destination.is_file()
    assert process.observation.operations is not None
    assert not any(op.kind=='provenance' for op in process.observation.operations)
    assert process.observation.transformation_provenance_output==()


@pytest.mark.parametrize('policy',['strict','tolerant'])
def test_cli_invalid_selected_metadata_aborts_and_exports_the_error(invoke,tmp_path,policy):
    """Rules: DK-GEN-09, DK-DIAG-04, DK-DIAG-05. Also §15 metadata errors."""
    destination=tmp_path/'out.ttl';report=tmp_path/'report.json'
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'none','metadata_file':fixture_path(METADATA,'metadata/partial_invalid/metadata.yaml'),'input_policy':policy},workdir=tmp_path,output_path=destination,diagnostics_path=report)
    assert process.returncode==3 and process.observation.outcome=='aborted' and process.observation.ontology is None
    assert not destination.exists()
    assert any(d.kind=='metadata_field' and d.severity=='ERROR' for d in process.observation.diagnostics)
    _report(invoke,report,process.observation)


@pytest.mark.parametrize('suffix',['json','ttl','ion'])
def test_cli_external_metadata_does_not_ingest_unaccepted_formats(invoke,tmp_path,suffix):
    """Rules: DK-GEN-09. Also §15 metadata-file control."""
    metadata=tmp_path/('metadata.'+suffix);metadata.write_text('{"title":"UNSUPPORTED_FORMAT_TITLE"}')
    process=invoke.cli(fixture_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'none','metadata_file':metadata,'input_policy':'best-effort'},workdir=tmp_path,output_path=tmp_path/'out.ttl',diagnostics_path=tmp_path/'report.json')
    assert process.conversion_started is not None
    if process.conversion_started:
        _report(invoke,tmp_path/'report.json',process.observation)
        if process.observation.ontology is not None:assert process.observation.external_metadata_output==()
    else:assert process.returncode==2 and process.observation.outcome is None

def test_cli_ontology_version_iri_sidecar_records_setting_and_final_byte_digest(invoke, tmp_path):
    """Rules: DK-IRI-01, DK-GEN-04, DK-GEN-10, DK-DIAG-04; RD-05 Option B replacement Rule 5; §15.

    Test-side options map to actual CLI controls at the replaceable boundary.
    Version/configuration evidence comes from delivered RDF, not the request.
    """
    import hashlib
    spdx = Namespace('http://spdx.org/rdf/terms#')
    source = fixture_path('shared/core_model')
    for index, version in enumerate(('https://example.test/versions/one', 'urn:directkg:test:version:two')):
        destination = tmp_path / f'versioned_{index}.ttl'
        process = invoke.cli(source, options={'base_iri': str(BASE), 'iri_strategy': 'id',
            'provenance': 'sidecar', 'ontology_version_iri': version}, workdir=tmp_path,
            output_path=destination, diagnostics_path=tmp_path / f'report_{index}.json')
        assert process.returncode == 0 and process.observation.outcome == 'completed'
        ontology = Graph().parse(destination, format='turtle')
        assert (ONTOLOGY, RDF.type, OWL.Ontology) in ontology
        assert (ONTOLOGY, OWL.versionIRI, URIRef(version)) in ontology
        assert (ONTOLOGY, OWL.imports, URIRef('https://w3id.org/directkg/vocab/dkgm')) in ontology
        sidecar = Graph().parse(destination.with_name(destination.stem + '.provenance.ttl'), format='turtle')
        observed = process.observation
        assert observed.provenance_roles is not None
        assert observed.provenance_roles.get('output') and observed.provenance_roles.get('configuration')
        output = observed.provenance_roles['output'][0]
        assert (output, DCTERMS.isFormatOf, ONTOLOGY) in sidecar
        checksums = [node for node in sidecar.objects(output, spdx.checksum)
                     if (node, spdx.algorithm, spdx.checksumAlgorithm_sha256) in sidecar]
        assert checksums
        for node in checksums:
            assert {str(value).lower() for value in sidecar.objects(node, spdx.checksumValue)} == {
                hashlib.sha256(destination.read_bytes()).hexdigest()}
        configuration = observed.provenance_roles['configuration'][0]
        assert (configuration, PROV.value, observed.configuration_literal) in sidecar
        assert isinstance(observed.configuration_literal, Literal)
        assert isinstance(yaml.safe_load(str(observed.configuration_literal)), dict)
        assert observed.configuration_controls is not None
        assert observed.configuration_controls.get('ontology_version_iri') == version

