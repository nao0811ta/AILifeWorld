using UnityEngine;
using System.Collections.Generic;

namespace MLPlayer {
	public class Action {
		public float rotate;
		public float forward;
		public float scale;
		public float jump;
		public bool canJump;
		public void Clear() {
			rotate = 0;
			forward = 0;
			jump = 0;
			canJump = false;
			scale = 1.0f;
		}

		public void Set(Dictionary<System.Object, System.Object> action) {
			
			// make hash table (because the 2 data arrays with equal content do not provide the same hash)
			var originalKey = new Dictionary<string, byte[]>();
			foreach (byte[] key in action.Keys) {
				originalKey.Add (System.Text.Encoding.UTF8.GetString(key), key);
				//Debug.Log ("key:" + System.Text.Encoding.UTF8.GetString(key) + " value:" + action[key]);
			}

			Clear ();
			forward = float.Parse(System.Text.Encoding.UTF8.GetString((byte[])action [originalKey ["x"]]));
			rotate = float.Parse(System.Text.Encoding.UTF8.GetString((byte[])action [originalKey ["y"]]));
			jump = float.Parse(System.Text.Encoding.UTF8.GetString((byte[])action [originalKey ["z"]]));
			scale = float.Parse(System.Text.Encoding.UTF8.GetString((byte[])action [originalKey ["s"]]));
			canJump = jump > 0.5;

		}
	}
}