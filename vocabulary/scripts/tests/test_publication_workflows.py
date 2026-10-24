"""Narrow control-flow regressions for the existing single Pages publisher."""
import copy
import unittest

import yaml

from test_publication import build


FETCH = "git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main"
GATE = "python vocabulary/scripts/build.py --check-only --publication"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        directory = build.ROOT / ".github/workflows"
        # BaseLoader preserves the YAML key 'on' rather than applying YAML 1.1's
        # boolean interpretation; GitHub treats it as a workflow trigger key.
        self.docs = yaml.load((directory / "docs.yml").read_text(), Loader=yaml.BaseLoader)
        self.vocabulary = yaml.load((directory / "publish-vocabulary.yml").read_text(), Loader=yaml.BaseLoader)

    def command(self, steps, text):
        found = [i for i, step in enumerate(steps) if step.get("run") == text]
        self.assertEqual(len(found), 1, f"Missing or ambiguous required workflow command: {text}")
        step = steps[found[0]]
        self.assertNotIn("if", step, "Required validation must not be conditionally bypassed")
        self.assertNotIn("continue-on-error", step)
        return found[0]

    def assert_documentation_gate(self, workflow):
        self.assertIn("workflow_call", workflow["on"])
        self.assertIn("workflow_dispatch", workflow["on"])
        steps = workflow["jobs"]["build"]["steps"]
        checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["fetch-depth"], "0")
        fetch = self.command(steps, FETCH)
        copy_index = next(i for i, step in enumerate(steps) if "cp -R vocabulary/latest vocabulary/versioned site/vocabulary/" in step.get("run", ""))
        gate = self.command(steps, GATE + " --site site")
        upload = next(i for i, step in enumerate(steps) if step.get("uses", "").startswith("actions/upload-pages-artifact@"))
        self.assertLess(fetch, gate)
        self.assertLess(copy_index, gate)
        self.assertLess(gate, upload)
        self.assertNotIn("continue-on-error", steps[upload])
        self.assertNotIn("if", steps[upload], "Upload must retain normal success-only behavior")
        deploy = workflow["jobs"]["deploy"]
        self.assertEqual(deploy["needs"], "build")
        self.assertEqual(deploy["if"], "github.ref == 'refs/heads/main'")
        publishers = [step for job in workflow["jobs"].values() for step in job.get("steps", [])
                      if step.get("uses", "").startswith("actions/deploy-pages@")]
        self.assertEqual(len(publishers), 1)

    def test_manual_and_reusable_documentation_paths_have_blocking_gates(self):
        self.assert_documentation_gate(self.docs)

    def test_validation_bypass_workflow_mutations_are_rejected(self):
        for mutation in ("missing", "skippable", "ignored failure", "early upload", "missing history", "unrestricted deployment"):
            with self.subTest(mutation=mutation):
                workflow = copy.deepcopy(self.docs)
                steps = workflow["jobs"]["build"]["steps"]
                gate = next(step for step in steps if step.get("run") == GATE + " --site site")
                if mutation == "missing":
                    steps.remove(gate)
                elif mutation == "skippable":
                    gate["if"] = "false"
                elif mutation == "ignored failure":
                    gate["continue-on-error"] = "true"
                elif mutation == "early upload":
                    steps.remove(gate)
                    steps.append(gate)
                elif mutation == "missing history":
                    steps[:] = [step for step in steps if step.get("run") != FETCH]
                else:
                    workflow["jobs"]["deploy"]["if"] = "true"
                with self.assertRaises(AssertionError):
                    self.assert_documentation_gate(workflow)

    def test_vocabulary_generation_and_promotion_are_gated(self):
        self.assertIn('feat/dkgm-identifier-migration', self.vocabulary['on']['push']['branches'])
        jobs = self.vocabulary["jobs"]
        validate = jobs["validate"]["steps"]
        self.command(validate, FETCH)
        generation = next(step for step in validate if "build.py" in step.get("run", ""))
        self.assertEqual(generation["run"], 'python vocabulary/scripts/build.py --publication --base "$BASE_SHA"')
        self.assertNotIn("continue-on-error", generation)
        prepare = jobs["prepare"]
        self.assertEqual(prepare["needs"], "validate")
        self.assertIn("github.ref == 'refs/heads/main'", prepare["if"])
        steps = prepare["steps"]
        fetch = self.command(steps, FETCH)
        generation = self.command(steps, "python vocabulary/scripts/build.py --publication")
        gate = self.command(steps, GATE)
        push = self.command(steps, "git push origin HEAD:main")
        self.assertLess(fetch, generation)
        self.assertLess(generation, gate)
        self.assertLess(gate, push)
        self.assertEqual(sum("git push" in step.get("run", "") for step in steps), 1)
        self.assertEqual(jobs["publish-site"]["needs"], "prepare")
        self.assertEqual(jobs["publish-site"]["uses"], "./.github/workflows/docs.yml")

    def test_verification_runs_only_after_successful_actual_deployment(self):
        jobs = self.docs["jobs"]
        output = jobs["deploy"]["outputs"]["deployed"]
        self.assertIn("steps.deployment.outcome == 'success'", output)
        self.assertIn("steps.current.outputs.publish == 'true'", output)
        verify = jobs["verify-publication"]
        self.assertEqual(verify["needs"], ["build", "deploy"])
        self.assertEqual(verify["if"], "needs.deploy.outputs.deployed == 'true'")
        self.assertEqual(verify["permissions"], {"contents": "read"})
        checkout = next(step for step in verify["steps"] if step.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["ref"], "${{ needs.build.outputs.source_sha }}")
        self.command(verify["steps"], "python vocabulary/scripts/verify_deployment.py")


if __name__ == "__main__":
    unittest.main()
