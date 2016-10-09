using UnityEngine;
using System.Collections.Generic;

namespace MLPlayer {
	public class Environment : MonoBehaviour {

		int itemCount1  = 4;
		int itemCount2  = 10; // add Naka
		float areaSize  = 15; // add Naka
		[SerializeField] List<GameObject> itemPrefabs;

		// Use this for initialization
		void Start () {
		
		}
		
		// Update is called once per frame
		void Update () {
		
		}

		public void OnReset() {
			foreach(Transform i in transform) {
				Destroy (i.gameObject);
			}
			for (int i=0; i<itemCount1; i++) { // fix Naka
			    	Vector3 pos = new Vector3 ((float)-0.3, 1, (float)24+4*i);

				pos += transform.position;
				GameObject obj = (GameObject)GameObject.Instantiate 
					(itemPrefabs[0], pos, Quaternion.identity);
				obj.transform.parent = transform;
			}
			for (int i=0; i<itemCount2; i++) { // add Naka
				Vector3 pos = new Vector3 (
					UnityEngine.Random.Range (-areaSize, areaSize),
					1,
					UnityEngine.Random.Range (-areaSize, areaSize));
//				Quaternion q = Quaternion.Euler (
//					UnityEngine.Random.Range (0f, 360f),
//					UnityEngine.Random.Range (0f, 360f),
//					UnityEngine.Random.Range (0f, 360f)
//					);

				pos += transform.position;
				int itemId = UnityEngine.Random.Range(0, itemPrefabs.Count);
				GameObject obj = (GameObject)GameObject.Instantiate 
					(itemPrefabs[itemId], pos, Quaternion.identity);
				obj.transform.parent = transform;
			}
			for (int i=0; i<itemCount2*3; i++) { // add Naka
				Vector3 pos = new Vector3 (
					UnityEngine.Random.Range (-areaSize+5, areaSize+5),
					1,
					UnityEngine.Random.Range ((areaSize+5)*2, (areaSize+5)*4));
//				Quaternion q = Quaternion.Euler (
//					UnityEngine.Random.Range (0f, 360f),
//					UnityEngine.Random.Range (0f, 360f),
//					UnityEngine.Random.Range (0f, 360f)
//					);

				pos += transform.position;
				GameObject obj = (GameObject)GameObject.Instantiate 
					(itemPrefabs[0], pos, Quaternion.identity);
				obj.transform.parent = transform;
			}

		}
	}
}
