"""Native-to-pixel provenance captured at the actual trusted renderer call.

Only fresh prepare installs this recorder. Existing evidence is never relabeled
from an arbitrary matching hash. A source cache hit is tied to its supplied
native path/hash and the cache's independently verified pixel hashes.
"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def resolved(path): return str(Path(path).resolve()).casefold()


class ProducerRecorder:
    def __init__(self, base):
        self.calls=[]
        for name in ('render_pdf','_render_office','_source_pages','_render_html'):
            original=getattr(base,name)
            def captured(path,*args,_original=original,_name=name,**kwargs):
                native=Path(path).resolve();before=sha(native)
                result=_original(path,*args,**kwargs)
                assert sha(native)==before,'Native changed during actual renderer invocation'
                pages=result[0] if _name=='_render_html' else result
                self.calls.append({'operation':_name,'native_path':str(native),
                    'native_sha256':before,'pages':[{'path':str(Path(p['path']).resolve()),
                    'sha256':p['sha256']} for p in pages]})
                return result
            setattr(base,name,captured)

    def bind(self,evidence,native_directory):
        """Require record identity AND exact observed native-to-pixel call."""
        native_directory=Path(native_directory).resolve()
        registry={}
        for role,key in [('input','sources'),('output','artifacts')]:
            for record in evidence.get(key,[]):
                relative=record['filename'] if role=='input' else record.get('relative_path',record['filename'])
                registry[record['evidence_id']]={'record':record,'role':role,
                    'relative':str(relative).replace('\\','/'),
                    'native':native_directory/'bundle'/Path(relative)}
        for image in evidence.get('visual_pages',[]):
            identity=image['evidence_id'].split(':V')[0]
            assert identity in registry,'Image has no exact native record identity'
            slot=registry[identity];record=slot['record'];native=slot['native']
            assert image.get('role')==slot['role'],'Image role differs from trusted native record'
            assert image.get('artifact')==record['filename'],'Image artifact label differs from trusted native record'
            assert str(image.get('relative_artifact','')).replace('\\','/')==slot['relative'],'Image relative label differs from trusted native record'
            assert sha(native)==record['sha256'],'Fresh native bundle differs from current registry'
            assert sha(image['path'])==image['sha256'],'Actual producer pixels changed'
            expected_input=native;expected_sha=record['sha256'];basis='EXACT_CURRENT_NATIVE_RENDER_INVOCATION'
            if str(image.get('view_semantics','')).startswith('SHEET_WIDE_VIEWPORT'):
                proof=next((v for v in record.get('render_views',[]) if v.get('view_id')==image.get('view_id')),None)
                assert proof and proof.get('original_sha256')==record['sha256']
                assert proof.get('original_values_and_styles_preserved') is True and proof.get('not_a_business_repair') is True
                assert proof.get('unchanged_unmodified_package_parts') is True
                assert proof.get('sheet_invariance') and all(s.get('data_formula_style_column_widths_identical') is True for s in proof['sheet_invariance'])
                expected_input=native_directory/'renders'/identity/'sheet_wide_source'/native.name
                expected_sha=proof['derived_sha256']
                assert sha(expected_input)==expected_sha==image.get('source_native_sha256'),'Derived renderer input differs from proven layout-only copy'
                basis='EXACT_LAYOUT_ONLY_DERIVATIVE_RENDER_INVOCATION_AND_NATIVE_INVARIANCE'
            matching=[c for c in self.calls if resolved(c['native_path'])==resolved(expected_input)
                and c['native_sha256']==expected_sha and any(resolved(p['path'])==resolved(image['path']) and p['sha256']==image['sha256'] for p in c['pages'])]
            if matching:
                # Prefer the outer native/cache render call, not a converted PDF.
                call=next((c for c in matching if c['operation']=='_source_pages'),matching[-1])
                operation=call['operation']
            else:
                assert image.get('renderer')=='Original-image-pixels' and resolved(image['path'])==resolved(native) and image['sha256']==expected_sha,'No trusted exact native-to-pixel producer call'
                operation='ORIGINAL_NATIVE_IMAGE_BYTES'
                basis='EXACT_CURRENT_NATIVE_IMAGE_BYTES_NO_RENDER_TRANSFORMATION'
            if image.get('source_native_sha256') is not None:
                assert image['source_native_sha256']==expected_sha,'Producer native SHA conflicts with existing metadata'
            else:
                image['source_native_sha256']=expected_sha
            image['producer_provenance']={'schema':'fresh-native-pixel-producer-binding-v3',
                'producer_source_sha256':sha(__file__),'operation':operation,
                'native_registry_id':identity,'role':slot['role'],'relative_artifact':slot['relative'],
                'current_original_native_sha256':record['sha256'],
                'actual_render_input_relative_to_native_capture':expected_input.relative_to(native_directory).as_posix(),
                'actual_render_input_sha256':expected_sha,'pixel_sha256':image['sha256'],
                'binding_basis':basis}
        evidence['render_images']=evidence['visual_pages']
        return {'schema':'fresh-renderer-invocations-v3','calls':copy.deepcopy(self.calls),
            'bound_image_count':len(evidence.get('visual_pages',[]))}
