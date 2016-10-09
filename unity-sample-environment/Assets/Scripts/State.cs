using UnityEngine;
using System.Collections;

namespace MLPlayer {
	public class State {
		public float reward;
		public bool endEpisode;
		public byte[][] image;
		public byte[][] depth;
		public float[][] gene;  // add Naka
		public float[] rewards; // add Naka
		public int agent_id;    // add Naka
		public float x_s; // add Nao x of scale
		public float y_s; // add Nao y of scale
		public float z_s; // add Nao z of scale
		public void Clear() {
			reward = 0;
			endEpisode = false;
			image   = null;
			depth   = null;
			rewards = null;
			x_s = y_s = z_s = 0;
		}
	}
}